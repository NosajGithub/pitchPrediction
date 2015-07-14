import random
import psycopg2
from sklearn.externals import joblib
from datetime import datetime
import os
from random import sample, seed
from collections import defaultdict, Counter
import pandas as pd
from sklearn.metrics import accuracy_score
import csv

def reservoir_sampling(N_population, n_samples):
    results = []
    for i, item in enumerate(N_population):
        if i < n_samples:
            results.append(item)
        else:
            k = random.randint(0, i)
            if k < n_samples:
                results[k] = item

    return results

def create_rs_conn(config):
    try:
        conn = psycopg2.connect(dbname=config['dbname'], host=config['host'], port=config['port'], user=config['user'], password=config['pwd'])
    except Exception as err:
        print err.code, err
    
    return conn

def get_available_rs_tables(cursor, *args, **kwargs):
    query = """select distinct(tablename) from pg_table_def where schemaname = 'public';"""
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def get_rs_atbat_data(cursor, *args, **kwargs):
    query = """
            select
                *
            from
                atbat
            """
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def get_rs_game_data(cursor, *args, **kwargs):
    query = """
            select
                *
            from
                game
            """
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def get_rs_hitchart_data(cursor, *args, **kwargs):
    query = """
            select
                *
            from
                hitchart
            """
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def get_rs_player_data(cursor, *args, **kwargs):
    query = """
            select
                *
            from
                player
            """
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def get_rs_pitch_data(cursor, *args, **kwargs):
    query = """
            select
                *
            from
                pitch
            """
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def run_rs_query(cursor, query):
    cur = cursor
    cur.execute(query)
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    return header, rows

def close_rs_conn(cursor, connection):
    try:
        cursor.close()
        connection.close()
    except Exception as err:
        print err.code, err
    
    return "Redshift connection successfully closed!"

def get_pitcher_sample(pitch_df, pitcher_id_col, sample_size = 25):
    '''Takes a Pandas DF with pitch data, samples a random subset of the pitchers present in the DF and returns the subset DF
    Input:
        pitch_df: Pandas DF with pitch data
        pitcher_id_col: string indicating the column in the DF that refers to the pitchers unique identifier
        sample_size: the number of pitchers to return (if greater than num of pitchers present, returns half of pitchers present in input DF)
    Output:
        Pandas DF with subset of pitchers' data'''
    
    #Get unique pitchers in DF
    pitchers = pitch_df[pitcher_id_col].unique()
    num_pitchers = len(pitchers)
    
    #Handle any outlier cases where sample size is too big
    if num_pitchers <= sample_size:
        if num_pitchers == 1:
            print 'only one pitcher detected in the dataset'
            return None
        else:
            sample_size = num_pitchers / 2
    
    #Randomly sample from all available pitchers and subset the DF down to rows including those pitchers
    pitcher_samp = sample(pitchers, sample_size)
    subset_df = pitcher_df[pitcher_df[pitcher_id_col].isin(pitcher_samp)]
    
    return subset_df

def collect_classifier_predictions(data_dict, **kwargs):
    """Given a data dictionary  containing 'train_data' and 'test_data' (as pandas DFs) and classifiers (kwargs),
    This runs the classifier and outputs the predictions of each classifier as a dictionary.
    Input:
        data_dict: the data dictionary containing all the train/test data/targets
        kwargs: sequence of classifiers (e.g. RF = RandomForest(), lin_svc = LinearSVC()...
    Output:
        dictionary of predictions where the key is the classifier label given in kwargs and the value is a list of predictions"""
    
    pred_dict = {}
    for classifier in kwargs.keys():
        
        # Fit a model on all the data and features
        kwargs[classifier].fit(data_dict['train_data'], data_dict['train_targets'])

        # Make predictions on dev data
        pred_dict[classifier] = kwargs[classifier].predict(data_dict['test_data'])
    
    # Return the dev performance score.
    return pred_dict

def ensemble_voting(predictions_dict):
    '''Takes in the predictions dictionary output from collect_classifier_predictions and returns pred with most votes'''
    
    #Instantiate an object to hold the combined scores from each classifier
    scores = defaultdict(list)
    
    #Run through each classifier and get voting predictions
    for classifier in predictions_dict.keys():
        
        for i, prediction in enumerate(predictions_dict[classifier]):
            scores[i].append(prediction)
    
    final_preds = []
    for i in sorted(scores):
        final_preds.append(Counter(scores[i]).most_common(1)[0][0])
    
    return pd.Series(final_preds, dtype = 'object')

def save_model(model, model_name, save_dir = 'models/', record_keeping_file = 'models/record_keeping.csv'):
    '''In order to manage our models, we need to keep track of where and when they came from. Each time
    this function is called, it serializes 'model' to a file called 'model_name'.pickle in a newly created folder located
    in 'save_dir' and writes a log of the event as a new line in 'record_keeping_file'

    Input:
        model: model object created using scikit-learn
        model_name: the name you'd like to give the model; this name will be the name of the new_folder
            created to house the model
        save_dir: the filepath of the directory in which to save the model (defaults to 'models/')
        record_keeping_file: the filepath of the file which keeps a record (name and date) of all created models
            (defaults to 'models/record_keeping.csv')
    '''
    
    #Create the new folder to house the model
    new_folder = save_dir + model_name
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    
    #Serialize the model
    complete_fp = new_folder + '/' + model_name + '.pickle'
    with open(complete_fp, 'wb') as f:
        joblib.dump(model, complete_fp)
    
    #Write the event to the record-keeping file (format = model_name, serialized_filepath, current_time)
    with open(record_keeping_file, 'a') as f:
        f.write(model_name + ',' + complete_fp + ',' + str(datetime.now()) + '\n')
    
    return

def run_classifier(classifier, data_dict):
    """Given a classifier and a data dictionary containing 'train_data' and 'test_data' (as pandas DFs),
    This runs the classifier and outputs the accuracy of the classifier on the test data."""
    
    # Fit a model on all the data and features
    classifier.fit(data_dict['train_data'], data_dict['train_targets'])

    # Make predictions on dev data
    dev_predictions = classifier.predict(data_dict['test_data'])
    
    # Return the dev performance score.
    return accuracy_score(data_dict['test_targets'], dev_predictions)

def randomly_sample_pitchers(cursor, num_pitchers = 5, min_pitch_count = 600, seed_num = None):
    '''Takes a random sample of pitchers from the db represented by "cursor" and returns a Pandas DF with
    the specified number ofpitchers who have thrown at least "min_pitch_count" pitches
    Input:
        cursor: DB handle
        num_pitchers: The number of pitchers whose data you want returned
        min_pitch_count: Minimum number of pitches a pitcher must have thrown in order to be considered in the 
            random sampling
        seed_num: If you want to be able to replicated the results, set a seed
    Output: Pandas DF containing pitch data for the randomly sampled pitchers'''
    
    cur = cursor
    
    #Get all pitchers meeting the min pitches criterion
    get_pitchers_query = '''SELECT pitcher, count(*)
                        FROM all_pitch_data
                        GROUP BY pitcher
                        HAVING count(*) >= %d''' % min_pitch_count
    cur.execute(get_pitchers_query)
    
    #Get all the pitcher ids and sample from them
    if seed_num is not None:
        seed(seed_num)
    
    pitcher_ids = [pitch_id for (pitch_id, counter) in cur.fetchall()]
    pitcher_id_sample = sample(pitcher_ids, num_pitchers)
    
    #Grab all pitch data from these pitchers
    get_pitches_query = '''SELECT *
                            FROM all_pitch_data
                            where pitcher in (%s)''' % str(pitcher_id_sample).strip('[]')
    cur.execute(get_pitches_query)
    
    #Create Pandas DF and return it
    rows = cur.fetchall()
    header = [colnames[0] for colnames in cur.description]
    pitcher_df = pd.DataFrame(rows)
    pitcher_df.columns = header
    
    return(pitcher_df)

def convert_same_pitches(pitch_df):
    '''According to http://www.beyondtheboxscore.com/2011/3/31/2068855/pitch-fx-primer, "FT" and "SI" are
    the same pitch and "KC" and "CU" are the same pitch.  This function takes a Pandas pitch DF and converts
    these pitch types to simply "FT" and "CU"
    Input:
        pitch_df: Pandas DF containing pitch_data with field "pitch_type"
    Output: Pandas DF with corrected pitch types'''
    
    pitch_df.pitch_type[pitch_df.pitch_type == 'FT'] = 'SI'
    pitch_df.pitch_type[pitch_df.pitch_type == 'KC'] = 'CU'
    
    return pitch_df

def load_model(model_name, record_keeping_file = 'models/record_keeping.csv'):
    '''This function takes in the name of a model and searches record_keeping_file
    for that name. It then tries to load and return the model (the last instance listed in record_keeping_file
    if there are more than one).  It requires that you run this function from the root directory of our project.
    
    Inputs:
        model_name: string of the model's name as it appears in record_keeping_file
        record_keeping_file: the filename of the file that holds the record keeping info for saved models
            (defaults to 'models/record_keeping.csv')
            
    Returns: De-serialized model matching the name of model_name    
    '''
    
    #open the record keeping file and get the filepath of the last instance where model_name occurs
    with open(record_keeping_file, 'rb') as f:
        reader = csv.reader(f, delimiter = ',')
        for row in reader:
            print row[0]
            if row[0] == model_name:
                model_fp = row[1]
    
    #Return the model
    return joblib.load(model_fp)