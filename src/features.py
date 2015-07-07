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

def prepare_score_diff_df(df):
    """Takes in a df with ALL pitches in games played by a particular pitcher, 
    then fills out the home and away runs 
    """
    
    class Score_Counter:
        def __init__(self):
            self.game_id = ""
            self.home_score = 0
            self.away_score = 0

        def get_score(self, game_id, score, home_score, away_score):
            # Initialize the counter at the start of a new game
            if self.game_id != game_id:
                self.home_score = 0
                self.away_score = 0
                self.game_id = game_id

            # Update if there's a score on this pitch
            if score == "T":
                self.home_score = home_score
                self.away_score = away_score

            return (self.home_score, self.away_score)
    
    home_scores = [] 
    away_scores = []
    s_counter = Score_Counter()
    
    df = df.sort(['game_id','num','id'])
    for index, row in df.iterrows():
        (home_score, away_score) = s_counter.get_score(row['game_id'],row['score'], \
                            row['home_team_runs'],row['away_team_runs'])
        home_scores.append(home_score)
        away_scores.append(away_score)
    
    df['home_score'] = home_scores
    df['away_score'] = away_scores
    
    return df

def make_score_diff(df):
    """Given a dataframe with home and away runs filled out, makes the
    score differential
    """
    df.loc[:,'score_diff'] = (df['home_score'] - df['away_score']) * \
    (df['half'].apply(lambda x: 1 if x == 'top' else -1))
    
    return df

def append_ingame_pitch_count(pitch_df):
	"""Add an ingame pitch count (number of cumulative pitches during appearance) for each pitch

    Args:
        pitch_df (df): Pandas dataframe of pitches across multiple games for one or more pitchers

    Returns:
        pitch_df (df): Pandas dataframe of pitches with additional ingame pitch count column
    """
	# Group pitches by pitcher and game and sort in time sequence
	pitch_df = pitch_df.sort(['pitcher', 'game_id', 'id'])
	pitch_grouped = pitch_df.groupby(['pitcher', 'game_id'])

	# Calculate and append ingame pitch count
	pitch_df['ingame_pitch_count'] = pitch_grouped.cumcount()

	return pitch_df

def append_season_pitch_count(pitch_df):
	"""Add a pitch count (number of cumulative pitches during season) for each pitch

    Args:
        pitch_df (df): Pandas dataframe of pitches across multiple games for one or more pitchers

    Returns:
        pitch_df (df): Pandas dataframe of pitches with additional ingame pitch count column
    """
    # Extract new column specifying season of game (year)
    pitch_df['season'] = pd.to_datetime(pitch_df.ix[:, 'date']).dt.year

	# Group pitches by pitcher and game and sort in time sequence
	pitch_df = pitch_df.sort(['pitcher', 'game_id', 'id'])
	pitch_grouped = pitch_df.groupby(['pitcher', 'season'])

	# Calculate and append season pitch count
	pitch_df['season_pitch_count'] = pitch_grouped.cumcount()

	return pitch_df

def append_previous_pitches_features(pitch_df):
	"""For each pitch, adds a set of features based on most recent (3) pitches

	For the start_speed, end_speed, break_y, break_angle, and break_length, returns
	the mean of the previous three pitches to append as separate columns. Also
	extracts the three previous pitches and adds them as separate features.

    Args:
        pitch_df (df): Pandas dataframe of pitches across multiple games for one or more pitchers

    Returns:
        pitch_df (df): Pandas dataframe of pitches with additional columns for added features
    """
	# Group pitches by pitcher and game and sort in time sequence
	pitch_df = pitch_df.sort(['pitcher', 'game_id', 'id'])
	pitch_grouped = pitch_df.groupby(['pitcher', 'game_id'])

	# Calculate and append mean start speed of last three pitches
	pitch_df['prev_pitches_mean_start_speed'] = pitch_grouped['start_speed'].apply(pd.rolling_mean, 3, min_periods=1).shift(1)
	pitch_df['prev_pitches_mean_end_speed'] = pitch_grouped['end_speed'].apply(pd.rolling_mean, 3, min_periods=1).shift(1)
	pitch_df['prev_pitches_mean_break_y'] = pitch_grouped['break_y'].apply(pd.rolling_mean, 3, min_periods=1).shift(1)
	pitch_df['prev_pitches_mean_break_angle'] = pitch_grouped['break_angle'].apply(pd.rolling_mean, 3, min_periods=1).shift(1)
	pitch_df['prev_pitches_mean_break_length'] = pitch_grouped['break_length'].apply(pd.rolling_mean, 3, min_periods=1).shift(1)
	pitch_df['last_pitch_type'] = pitch_grouped['pitch_type'].shift(1)
	pitch_df['second_last_pitch_type'] = pitch_grouped['pitch_type'].shift(2)
	pitch_df['third_last_pitch_type'] = pitch_grouped['pitch_type'].shift(3)

	return pitch_df
	
def make_features(df):
    """Given a pandas dataframe with all the pitches for a single pitcher, 
    make all the features
    """
    
    df = pitcher_priors(df)
    df = make_score_diff(df)
    # Add more feature creation functions here
    
    return df