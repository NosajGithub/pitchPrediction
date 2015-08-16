from logging import getLogger, Handler
from urllib import urlopen
from warnings import simplefilter
from time import sleep
from xml.dom import minidom
from bs4 import BeautifulSoup
from re import search
import pandas as pd 
from src.features import *
import urllib2
from collections import defaultdict

from datetime import date, timedelta
# import datetime

from src.features import *
from src.utils import *
from src.validation import *
from src.exploration import *


class NullHandler(Handler):
    def emit(self, record):
        pass

class CONSTANTS:
    BASE = 'http://gd2.mlb.com/components/game/mlb/'
    FETCH_TRIES = 10

class Fetcher:
    @classmethod
    def fetch(self, url):
        for i in xrange(CONSTANTS.FETCH_TRIES):
            logger.debug('FETCH %s' % url)
            try:
                page = urlopen(url)
            except IOError, e:
                if i == CONSTANTS.FETCH_TRIES-1:
                    logger.error('ERROR %s (max tries %s exhausted)' % (url, CONSTANTS.FETCH_TRIES))
                sleep(1)
                continue

            if page.getcode() == 404:
                return None
            else:
                return page.read()
            break

logger = getLogger('gameday')
logger.addHandler(NullHandler())

class Pitch:
    def __init__(self, element, count, **kwargs):

        values = {}
        values['num'] = kwargs['num'] if 'num' in kwargs else None
        values['game_id'] = kwargs['game_id'] if 'game_id' in kwargs else None
        values['pitcher'] = kwargs['pitcher'] if 'pitcher' in kwargs else None
        values['batter'] = kwargs['batter'] if 'batter' in kwargs else None
        values['b'] = count['balls']
        values['s'] = count['strikes']
        
        # these change a lot :(
        # tired of taking them from the XML element
        # because maybe I don't have them in the schema
        FIELDS = ['des','id','type','x','y','on_1b','on_2b','on_3b','sv_id','start_speed',
            'end_speed','sz_top','sz_bot','pfx_x','pfx_z','px','pz','x0','y0','z0','vx0','vy0','vz0',
            'ax','ay','az','break_y','break_angle','break_length','pitch_type','type_confidence',
            'spin_dir','spin_rate','zone']

        for key in element.attributes.keys():
            if key in FIELDS:
                values[key] = element.attributes[key].value
        
        self.values = values

class AtBats(list):
    
    def save(self):

        AB_FIELDS = ['inning','num','p_throws','event','score','away_team_runs','start_tfs_zulu','start_tfs',
                  'pitcher','batter','half','game_id','b_height','home_team_runs','des','o','stand','event2']

        P_FIELDS = ['des','id','type','x','y','on_1b','on_2b','on_3b','sv_id','start_speed',
            'end_speed','sz_top','sz_bot','pfx_x','pfx_z','px','pz','x0','y0','z0','vx0','vy0','vz0',
            'ax','ay','az','break_y','break_angle','break_length','pitch_type','type_confidence',
            'spin_dir','spin_rate','zone', 'num','game_id','b','s']
        
        ab_values = dict((k,[]) for k in AB_FIELDS)
        p_values = dict((k,[]) for k in P_FIELDS)
                
        for inning in self:
            for atbat in inning:
                for key in ab_values.keys():
                    ab_values[key].append(atbat.get(key,None))
                
                for pitch in atbat['pitches']:
                    for key in p_values.keys():
                        p_values[key].append(pitch.values.get(key,None))

        result = pd.merge(pd.DataFrame(ab_values), pd.DataFrame(p_values), how='inner', on=['num','game_id'])
        
        # Cast variables appropriately
        result['pitcher'] = result['pitcher'].astype('int64')
        result['zone']= result['zone'].astype('float64')
        result['s']= result['s'].astype('int64')
        result['on_3b']= result['on_3b'].astype('float64')
        result['on_2b']= result['on_2b'].astype('float64')
        result['on_1b']= result['on_1b'].astype('float64')
        result['o']= result['o'].astype('int64')
        result['home_team_runs']= result['home_team_runs'].astype('float64')
        result['batter']= result['batter'].astype('int64')
        result['b']= result['b'].astype('int64')
        result['away_team_runs']= result['away_team_runs'].astype('float64')
        result['id'] = result['id'].astype('int64')
        result['num'] = result['num'].astype('int64')
        
        result['des'] = result['des_y']
        result['date'] = self.game_date
        
        return result

        
    def __init__(self, gid, game_id):
        super(AtBats,self).__init__()

        self.game_date = "-".join(gid.split("_")[1:4])

        year, month, day = gid.split('_')[1:4]
        url = '%syear_%s/month_%s/day_%s/%s/inning/' % (CONSTANTS.BASE, year, month, day, gid)        
        
        contents = Fetcher.fetch(url)
        if contents is None:
            return
        
        soup = BeautifulSoup(contents, "lxml")

        inning_num = 1
        for inning_link in soup.findAll('a'):
            if search(r'inning_\d+\.xml', inning_link['href']):
                inning_url = '%s%s' % (url, inning_link['href'])
                doc = minidom.parseString(Fetcher.fetch(inning_url))
                
                inning = []
                
                for atbat in doc.getElementsByTagName('atbat'):
                    values = {}
                    half = atbat.parentNode.nodeName
                    for key in atbat.attributes.keys():
                        values[str(key)] = atbat.attributes[key].value

                    values['half'] = half
                    values['game_id'] = game_id
                    values['inning'] = inning_num
                    values['pitches'] = []
                    
                    balls = 0
                    strikes = 0
                    for pitch in atbat.getElementsByTagName('pitch'):
                        count = {'balls': balls, 'strikes': strikes}
                        kwargs = {'game_id': game_id,
                            'batter': values['batter'],
                            'pitcher': values['pitcher'],
                            'num': atbat.attributes['num'].value}
                        p = Pitch(pitch, count, **kwargs)
                        values['pitches'].append(p)

                        if pitch.attributes['type'].value == 'B':
                            balls = balls + 1
                        elif pitch.attributes['type'].value == 'S':
                            strikes = strikes + 1

                    inning.append(values)
                self.append(inning)
                inning_num += 1


def get_batters(gid = 'gid_2015_07_24_oakmlb_sfnmlb_1'):
    year, month, day = gid.split('_')[1:4]
    url = '%syear_%s/month_%s/day_%s/%s/%s' % ('http://gd2.mlb.com/components/game/mlb/', year, month, day, gid, 'players.xml')

    contents = Fetcher.fetch(url)
    if contents is None:
        return
       
    soup = BeautifulSoup(contents, 'lxml')

    def get_players(soup):
        d = defaultdict(list)    
        for player in soup.find_all("player"):
            if player.get('bat_order',None) is not None:
                d['id'].append(player['id'])
                d['first'].append(player['first'])
                d['last'].append(player['last'])
                d['bat_order'].append(player['bat_order'])
                d['bats'].append(player['bats'])

        return pd.DataFrame(d)

    away = soup.game.team
    home = soup.game.team.next_sibling.next_sibling

    away_batters = get_players(away)
    home_batters = get_players(home)

    return (away_batters, home_batters)

def get_pitcher_df_for_realtime(pitcher_id, binarize_pitches = True, cols_of_interest = None, date_subsetting = True, pitch_df = None, new_pitches = None):
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
        new_pitches: a dataframe of pitches from the current game to append to the pitcher's past pitches
    Returns: A Pandas dataframe containing only columns which are useful for modeling
    """
        
    # Append new data to old data
    pitch_df = pitch_df.set_index(['game_id','num','id'])
    new_pitches = new_pitches.set_index(['game_id','num','id'])

    pitch_df = pitch_df.append(new_pitches)
    pitch_df = pitch_df.reset_index()
    pitch_df.sort(['game_id','num','id'])
    
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
    # print to_be_removed, "rows didn't contain pitch metadata and were removed"
    
    #Binarize the on-base variables
    pitch_df = binarize_on_base(pitch_df)
    
    #Get rid of columns that aren't useful for modeling
#     cols_to_exclude = [u'game_id', u'num', u'pitcher', u'batter',
#                     u'des', u'id', u'type', u'x', u'y', u'sv_id',
#                     u'start_speed', u'end_speed', u'sz_top', u'sz_bot',
#                     u'pfx_x', u'pfx_z', u'px', u'pz', u'x0', u'y0', 
#                     u'z0', u'vx0', u'vy0', u'vz0', u'ax', u'ay', u'az', 
#                     u'break_y', u'break_angle', u'break_length', 
#                     u'type_confidence', u'spin_dir', u'spin_rate', u'zone',
#                     u'half', u'inning', u'score', u'b_height', 
#                     u'event', u'event2', u'event3', u'home_team_runs', 
#                     u'away_team_runs', u'p_first_name', u'p_last_name', 
#                     u'p_height', u'pitcher_dob', u'b_first_name', 
#                     u'b_last_name', u'batter_dob', u'game_type', 
#                     u'local_game_time', u'game_pk', u'game_time_et', 
#                     u'home_id', u'home_fname', u'away_id', u'away_fname',
#                     u'status_ind', u'day','home_score','away_score']
#     pitch_df = pitch_df.drop(cols_to_exclude, axis = 1)
        
#     #Check to see if the user has specified additional cols to drop
#     if exclude_cols is not None:
#         pitch_df = pitch_df.drop(exclude_cols, axis = 1)

    if cols_of_interest is not None:
        pitch_df = pitch_df.loc[:,cols_of_interest]

    #Recategorize some variables that couldn't be calculated
    pitch_df['last_pitch_type'].loc[pitch_df['last_pitch_type'].isnull()] = 'not_available'
    pitch_df['second_last_pitch_type'].loc[pitch_df['second_last_pitch_type'].isnull()] = 'not_available'
    pitch_df['third_last_pitch_type'].loc[pitch_df['third_last_pitch_type'].isnull()] = 'not_available'
    
    #Convert 'season' to a categorical indicating current season (or not)
    if u'season' in pitch_df.columns:
        pitch_df['cur_season'] = np.where(pitch_df['season'] == pitch_df['season'].max(), 1, 0)
        pitch_df.drop('season', axis = 1, inplace = True)
    
    #Get rid of any rows that contain NAs
    num_of_na = pitch_df.isnull().any(axis = 1).sum()
    pitch_df = pitch_df.dropna()
    # print num_of_na, "rows contained at least 1 NaN and were dropped"
    
    return pitch_df


class Prediction_Machine:
    """ Class to take in the historical data and then combine it with new data in order to output new predictions"""

    def __init__(self, pitcher, pitch_df, game_date):
    
        # Create a list of the columns that we're interested in using as features
        self.cols_of_interest = ([u'b', u's', u'on_1b', u'on_2b', u'on_3b', u'o',
                         u'stand', u'Not_Fastball_pb_prior', u'Not_Fastball_pbs_prior', 
                         u'Fastball_pb_prior', u'Fastball_pbs_prior', u'Not_Fastball_pc_prior', 
                         u'Not_Fastball_pcs_prior', u'Fastball_pc_prior', u'Fastball_pcs_prior', 
                         u'Not_Fastball_pg_prior', u'Not_Fastball_pgs_prior', 
                         u'Fastball_pg_prior', u'Fastball_pgs_prior',
                         u'prev_pitches_mean_start_speed', u'prev_pitches_mean_end_speed',
                         u'prev_pitches_mean_break_y', u'prev_pitches_mean_break_angle',
                         u'prev_pitches_mean_break_length', u'ingame_pitch_count', u'cur_season', u'season_pitch_count',
                         u'season', u'last_pitch_type', u'second_last_pitch_type', u'third_last_pitch_type', u'date',
                         u'pitch_type'])
        
        self.cols_of_interest2 = ([u'b', u's', u'on_1b', u'on_2b', u'on_3b', u'o',
                     u'stand_L', u'Not_Fastball_pb_prior', u'Not_Fastball_pbs_prior', 
                     u'Fastball_pb_prior', u'Fastball_pbs_prior', u'Not_Fastball_pc_prior', 
                     u'Not_Fastball_pcs_prior', u'Fastball_pc_prior', u'Fastball_pcs_prior', 
                     u'Not_Fastball_pg_prior', u'Not_Fastball_pgs_prior', 
                     u'Fastball_pg_prior', u'Fastball_pgs_prior', u'last_pitch_type_Fastball', 
                     u'last_pitch_type_Not_Fastball',u'last_pitch_type_not_available', 
                     u'second_last_pitch_type_Fastball',u'second_last_pitch_type_Not_Fastball',
                     u'second_last_pitch_type_not_available', u'third_last_pitch_type_Fastball',
                     u'third_last_pitch_type_Not_Fastball', u'third_last_pitch_type_not_available', 
                     u'prev_pitches_mean_start_speed', u'prev_pitches_mean_end_speed',
                     u'prev_pitches_mean_break_y', u'prev_pitches_mean_break_angle',
                     u'prev_pitches_mean_break_length', u'ingame_pitch_count', u'cur_season', u'season_pitch_count'])

        self.pitcher = pitcher
        self.pitch_df = pitch_df
        self.game_date = game_date

    def get_new_pred(self, new_pitches):
        """Takes in a set of real-time pitches and outputs the predictions and the targets"""

        pitcher_df = get_pitcher_df_for_realtime(pitcher_id = self.pitcher, 
                                                    cols_of_interest = self.cols_of_interest, 
                                                    date_subsetting = False, pitch_df = self.pitch_df, 
                                                    new_pitches= new_pitches)

        #Create a split with training on everything before today's game
        subset_date = datetime.strptime(self.game_date, "%Y-%m-%d") - timedelta(days=1)
        modeling_data = split_test_train(pitcher_df, subset_date)

        #Subset the dataframe down to the columns of interest
        baseline_dict = subset_data(modeling_data, self.cols_of_interest2)

        #Run 4 classifiers on the data (returns dictionary containing all fitted classifiers)
        classifier_dict = run_all_classifiers(baseline_dict)

        lin_svc_preds = classifier_dict['lin_svc'].predict(baseline_dict['test_data'])

        return lin_svc_preds, baseline_dict['test_targets']