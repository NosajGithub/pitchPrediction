import random


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
	
def get_pitcher_sample(pitch_df, pitcher_id_col, sample_size = 25):
    '''Takes a Pandas DF with pitch data, samples a random subset of the pitchers present in the DF and returns the subset DF
    Input:
        pitch_df: Pandas DF with pitch data
        pitcher_id_col: string indicating the column in the DF that refers to the pitchers unique identifier
        sample_size: the number of pitchers to return (if greater than num of pitchers present, returns half of pitchers present in input DF)
    Output:
        Pandas DF with subset of pitchers' data'''
    
    from random import sample
    
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
    
    from collections import defaultdict, Counter
    
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