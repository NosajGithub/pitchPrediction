import pandas as pd
import numpy as np
from utils import run_rs_query

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

def roll_forward_outs(group):
    '''Function called in "fix_outs" which is applied to each grouping to correct the number of outs'''
    
    #Get the unique atbats
    unique_at_bats = group['num'].unique()
    
    #Loop through batters from end of inning to beginning
    for i in reversed(range(1, len(group['num'].unique()))):
        
        group.loc[group['num'] == unique_at_bats[i], 'o'] = group['o'][group['num'] == unique_at_bats[i - 1]].unique()[0]
    
    #Set the outs for the first batter of the inning ot 0
    group.loc[group['num'] == unique_at_bats[0], 'o'] = 0
    return group

def fix_outs(pitch_df):
    '''Rolls outs forward one batter
    Input:
        pitch_df: Pandas dataframe containing joined pitch/atbat/game data
    Output: Pandas df with the outs adjusted to be indicative of the game state at the time of the pitch
    '''
    
    #Group the dataframe by game, inning, and half
    pitch_df = pitch_df.sort(['game_id', 'inning', 'half', 'num'])
    grouped = pitch_df.groupby(['game_id', 'inning', 'half'])
    
    #Roll forward the outs
    pitch_df = grouped.apply(roll_forward_outs)
    
    return pitch_df

def binarize_on_base(df):
    
    df['on_1b'] = np.where(df['on_1b'].isnull(), 0, 1)
    df['on_2b'] = np.where(df['on_2b'].isnull(), 0, 1)
    df['on_3b'] = np.where(df['on_3b'].isnull(), 0, 1)
    
    return df
	
def make_features(df):
    """Given a pandas dataframe with all the pitches for a single pitcher, 
    make all the features
    """
    
    #Jason's features
    df = pitcher_priors(df)
    df = make_score_diff(df)

    #Alan's features
    df = append_ingame_pitch_count(df)
    df = append_season_pitch_count(df)
    df = append_previous_pitches_features(df)

    #Zach's features
    df = fix_outs(df)
    # Add more feature creation functions here
    
    return df

def get_pitcher_df_for_modeling(cur, pitcher_id, binarize_pitches = True, exclude_cols = None, date_subsetting = True):
    """
    This function takes in a pitcher's ID and creates a data frame that is ready for modeling.  The features
    created with this function or determined by the 'make_features' function.

    Inputs:
        cur: Redshift db cursor
        pitcher_id: numeric pitcher id
        binarize_pitches: indicates whether or not the pitches should be split into Fastball/Offspeed or not
        exclude_cols: List of strings of any additional columns to exclude from the df that's returned
        date_subsetting: Boolean that determines whether or not to subset the data based on our
        data integrity issue with missing games
    Returns: A Pandas dataframe containing only columns which are useful for modeling
    """
    
    #Get the pitchers info from redshift and stor it
    raw_query = """SELECT * FROM all_pitch_data \
    WHERE game_id IN \
    (SELECT DISTINCT game_id FROM all_pitch_data \
    WHERE pitcher = %d)
    """ % pitcher_id
    sample_header, sample_rows = run_rs_query(cur, raw_query)
    pitch_df = pd.DataFrame(sample_rows)
    pitch_df.columns = sample_header
    
    
    # Add the home and away score at the pitch level to set up score_diff
    pitch_df = prepare_score_diff_df(pitch_df)
    
    # Limit to only the pitcher in question
    pitch_df = pitch_df[pitch_df['pitcher'] == pitcher_id]
    
    #Convert the date to a pandas datetime object
    pitch_df['date'] = pd.to_datetime(pitch_df['date'], '%Y-%m-%d')
    
    #Subset down to dates with correct data, if applicable
    if date_subsetting:
        #subset down after 2008 and before 2013 because of data integrity issues
        pitch_df = pitch_df[(pitch_df['date'] >= '2009-01-01') &
                            (pitch_df['date'] <= '2013-01-01')]
    
    #Binarize pitch type, if applicable
    if binarize_pitches:
        pitch_df['pitch_type'] = np.where(pitch_df['pitch_type'].isin(['FA', 'FF', 'FT', 'FC', 'FS', 'SI', 'SF']), 
                                              'Fastball', 
                                              'Not_Fastball')
        
    #Make all the features encapsulated in the 'make_features' function
    pitch_df = make_features(pitch_df)
    
    #Remove pitches not containing metadata and tell the user how many were removed
    to_be_removed = len(pitch_df[pitch_df['type_confidence'].isnull()])
    pitch_df = pitch_df[pitch_df['type_confidence'].notnull()]
    print to_be_removed, "rows didn't contain pitch metadata and were removed"
    
    #Binarize the on-base variables
    pitch_df = binarize_on_base(pitch_df)
    
    #Get rid of columns that aren't useful for modeling
    cols_to_exclude = [u'game_id', u'num', u'pitcher', u'batter',
                    u'des', u'id', u'type', u'x', u'y', u'sv_id',
                    u'start_speed', u'end_speed', u'sz_top', u'sz_bot',
                    u'pfx_x', u'pfx_z', u'px', u'pz', u'x0', u'y0', 
                    u'z0', u'vx0', u'vy0', u'vz0', u'ax', u'ay', u'az', 
                    u'break_y', u'break_angle', u'break_length', 
                    u'type_confidence', u'spin_dir', u'spin_rate', u'zone',
                    u'half', u'inning', u'score', u'b_height', 
                    u'event', u'event2', u'event3', u'home_team_runs', 
                    u'away_team_runs', u'p_first_name', u'p_last_name', 
                    u'p_height', u'pitcher_dob', u'b_first_name', 
                    u'b_last_name', u'batter_dob', u'game_type', 
                    u'local_game_time', u'game_pk', u'game_time_et', 
                    u'home_id', u'home_fname', u'away_id', u'away_fname',
                    u'status_ind', u'day','home_score','away_score','p_throws_L']
    pitch_df = pitch_df.drop(cols_to_exclude, axis = 1)
    
    #Check to see if the user has specified additional cols to drop
    if exclude_cols is not None:
        pitch_df = pitch_df.drop(exclude_cols, axis = 1)
    
    #Recategorize some variables that couldn't be calculated
    pitch_df['last_pitch_type'].loc[pitch_df['last_pitch_type'].isnull()] = 'not_available'
    pitch_df['second_last_pitch_type'].loc[pitch_df['second_last_pitch_type'].isnull()] = 'not_available'
    pitch_df['third_last_pitch_type'].loc[pitch_df['third_last_pitch_type'].isnull()] = 'not_available'
    
    #Get rid of any rows that contain NAs
    num_of_na = pitch_df.isnull().any(axis = 1).sum()
    pitch_df = pitch_df.dropna()
    print num_of_na, "rows contained at least 1 NaN and were dropped"
    
    return pitch_df