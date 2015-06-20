import random
import psycopg2


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