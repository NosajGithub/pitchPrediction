import pandas as pd
import numpy as np

class Prior_Counter:
    def __init__(self, pitch_list):
        pitch_store = {}
        global_pitch_store = {}

        # Make dicts to hold output columns
        priors = {}
        priors_shrunk = {}

        # Make empty lists in dicts 
        for pitch in pitch_list:
            priors[pitch] = []
            priors_shrunk[pitch] = []

        # Initialize global_pitch_store
        for pitch in pitch_list:
            global_pitch_store[pitch] = 0
        global_pitch_store['total'] = 0
        
        # Store dicts and beta
        self.pitch_store = pitch_store
        self.global_pitch_store = global_pitch_store
        self.priors = priors
        self.priors_shrunk = priors_shrunk
        self.beta = 4.0
        
    def update(self, pitch_type, cur_factor):
        """Given a pitch_type and this pitch's factor, writes 
        out the current probabilities to the priors dicts 
        and then adds the current pitch type to the pitch stores 
        """

        if not cur_factor in self.pitch_store:
            self.pitch_store[cur_factor] = dict(total = 0)

        ### Write priors to output lists ###
            
        # If factor has never been seen before, 
        # append 0 (non-shrunk) or global averages (shrunk)
        cur_factor_total = self.pitch_store[cur_factor]['total']
        global_pitch_store_total = self.global_pitch_store['total']
        
        if cur_factor_total == 0:
            # If it's the first pitch in the dataframe
            if global_pitch_store_total == 0:
                for ptype in self.priors:
                    self.priors[ptype].append(0.0)
                    self.priors_shrunk[ptype].append(0.0)
            else:
                for ptype in self.priors:
                    self.priors[ptype].append(0.0)
                    self.priors_shrunk[ptype].append(
                        self.global_pitch_store[ptype] / (global_pitch_store_total*1.0)
                    )

        # If you've seen the factor before, append the past frequency (non-shrunk)
        # or the shrunk past frequency (shrunk)
        else:
            for ptype in self.priors:
                cur_pitch_freq = self.pitch_store[cur_factor].get(ptype,0)
                cur_pitch_freq_global = self.global_pitch_store[ptype]
                
                self.priors[ptype].append(cur_pitch_freq / (cur_factor_total*1.0))
                self.priors_shrunk[ptype].append(

                    # Shrunk formula
                    (cur_pitch_freq * (cur_pitch_freq / (cur_factor_total * 1.0)) + # n * s +
                    self.beta * (cur_pitch_freq_global / (global_pitch_store_total * 1.0))) # B * p
                    / ((cur_pitch_freq + self.beta) * 1.0) # / n + B
                )
        
        ### Update pitch_stores with the current pitch's type ###
        
        # Update pitch_store
        if not pitch_type in self.pitch_store[cur_factor]:
            self.pitch_store[cur_factor][pitch_type] = 1
        else:
            self.pitch_store[cur_factor][pitch_type] += 1
        self.pitch_store[cur_factor]['total'] += 1            
    
        # Update global_pitch_store
        self.global_pitch_store[pitch_type] += 1
        self.global_pitch_store['total'] += 1
        
    def add_to_df(self, df, suffix):
        """Given a dataframe and a suffix, adds the counter's accumulated data to the dataframe"""
        for ptype in self.priors:
            df[str(ptype) + suffix + "_prior"] = self.priors[ptype]
            df[str(ptype) + suffix + "s_prior"] = self.priors_shrunk[ptype]
    
        return df

def pitcher_priors(df):
    """Given a pandas dataframe containing all pitches for a single pitcher, 
    returns the dataframe with all priors and shrunk priors;
    Uses columns pitch table columns: pitch_type, b, s, batter, game_id, num and id
    """
    
    pitch_list = df['pitch_type'].unique()
    pb_counter = Prior_Counter(pitch_list) # pitcher-batter priors
    pc_counter = Prior_Counter(pitch_list) # pitcher-count priors
    pg_counter = Prior_Counter(pitch_list) # pitcher-game priors
    
    # Iterate through dataframe, updating stores and making features
    df = df.sort(['game_id','num','id'])
    for index, row in df.iterrows():
        pitch_type = row['pitch_type']
        cur_count = str(row['b']) + "-" + str(row['s'])
        cur_batter = row['batter']
        cur_game = row['game_id']
        
        pb_counter.update(pitch_type, cur_batter)
        pc_counter.update(pitch_type, cur_count)
        pg_counter.update(pitch_type, cur_game)
    
    df = pb_counter.add_to_df(df,"_pb")
    df = pc_counter.add_to_df(df,"_pc")
    df = pg_counter.add_to_df(df,"_pg")
    return df

def append_ingame_pitch_count(pitch_df):
	"""Add an ingame pitch count (number of cumulative pitches during appearance) for each pitch

    Args:
        pitch_df (df): Pandas dataframe of pitches across multiple games for one or more pitchers

    Returns:
        pitch_df (df): Pandas dataframe of pitches with additional ingame pitch count column
    """
    # Add column tracking sum of balls and strikes
    pitch_df['temp'] = pitch_df['s'] + pitch_df['b'] + 1
	
	# Group pitches by pitcher and game and sort in time sequence
	pitch_df = pitch_df.sort(['pitcher', 'game_id', 'num', 'temp'])
	pitch_grouped = pitch_df.groupby(['pitcher', 'game_id'])

	# Calculate and append ingame pitch count
	pitch_df['pitch_count'] = pitch_grouped.cumcount()

	pitch_df = pitch_df.drop('temp', axis=1)
	return pitch_df
	

def make_features(df):
    """Given a pandas dataframe with all the pitches for a single pitcher, 
    make all the features
    """
    
    df = pitcher_priors(df)
    
    # Add more feature creation functions here
    
    return df