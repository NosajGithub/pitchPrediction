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