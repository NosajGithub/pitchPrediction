#import necessary libraries
import numpy as np
import pandas as pd

from config import REDSHIFT_CONFIG
from features import *
from utils import *
from exploration import *

#Define the class
from datetime import date

class Pitcher:
    '''Master class to contain all info/methods related to a pitcher's pitch data'''
    
    def __init__(self, pitcher_id, redshift_cursor, table = None):
        '''Stores:
            -a database cursor (self.cur)
            -pitcher ID (self.pitcher_id)
            -all pitcher data (self.data) from 'table' (all_pitch_data by default)
        '''
        
        #Store the pitcher's id
        self.pitcher_id = pitcher_id
        
        #Using a passed-in cursor instead of creating it here, so we don't have to open new connection
        #for each pitcher we create
        self.cur = redshift_cursor
        
        #Use exception handling in case we get a shutdown of the connection
        try:
            #Choose which table to pull data from
            if table is None:
                self.data = get_pitcher_df_for_modeling(self.cur, 
                                                        pitcher_id = pitcher_id, 
                                                        date_subsetting = False)
            else:
                self.data = get_pitcher_df_for_modeling(self.cur, 
                                                        pitcher_id = pitcher_id, 
                                                        date_subsetting = False,
                                                        table = table)
        except:
            # Re-establish a connection to the redshift database
            conn = create_rs_conn(config=REDSHIFT_CONFIG)
            self.cur = conn.cursor()
            
            #Choose which table to pull data from
            if table is None:
                self.data = get_pitcher_df_for_modeling(self.cur, 
                                                        pitcher_id = pitcher_id,
                                                        date_subsetting = False)
            else:
                self.data = get_pitcher_df_for_modeling(self.cur, 
                                                        pitcher_id = pitcher_id, 
                                                        date_subsetting = False,
                                                        table = table)
        
        #Get the pitcher's name
        self.cur.execute('''select p_first_name, p_last_name
                    from all_pitch_data
                    where pitcher = %d
                    limit 1''' % self.pitcher_id)
        self.name = " ".join(self.cur.fetchall()[0])
        
        #initiate a list that keeps track of methods called on the object (record-keeping)
        self.method_history = []    
            
    def find_optimal_date_splits(self):
        '''Jason's code here'''
        self.method_history.append("split_test_train")
        
    def subset_data_by_date(self, max_date = None, min_date = '2008-01-01'):
        '''Subsets self.data based on max and min dates'''
        
        #Get a max_date if one not given
        if max_date is None:
            self.max_date = date.today().strftime('%Y-%m-%d')
        else:
            self.max_date = max_date
        
        #Store the minimum date
        self.min_date = min_date
        
        #Subset the data
        self.data = self.data[(self.data['date'] <= self.max_date) & (self.data['date'] >= self.min_date)]
        
        #Indicate that the method has been called
        self.method_history.append('subset_by_date')
        
    def subset_data_by_columns(self, cols):
        '''self.data is subset to only include "cols"'''
        self.modeling_dict['train_data'] = self.modeling_dict['train_data'][cols]
        self.modeling_dict['test_data'] = self.modeling_dict['test_data'][cols]
        self.method_history.append("subset_by_columns")
    
    def split_test_train(self, quantile_split = 0.9, date_override = None):
        '''Splits self.data into testing and train data, creating a new dictionary containing all the
        test/train data and targets'''
        
        #Get the date on which to split test/train
        if date_override is None:
            split_date = str(self.data['date'].quantile(quantile_split))[:10]
            
        else:
            split_date = date_override
        
        #split the data and return a dictionary with test/train data/targets
        self.modeling_dict = split_test_train(self.data, split_date)
        
        #Log the transaction
        self.method_history.append("split_test_train_" + split_date)
        
        #Store the baseline accuracy
        self.baseline_accuracy = naive_accuracy(self.modeling_dict)
        
    def pitch_type_by_year(self):
        '''returns a pandas dataframe getting the count of the pitch types by year'''
        return get_pitch_types_by_year(self.data, use_gameday = False)
    
    def run_classifiers(self):
        '''runs four different classifiers and tries to ensemble them'''
        
        classifier_dict = run_all_classifiers(self.modeling_dict)
        all_predictions_dict = collect_classifier_predictions2(self.modeling_dict, classifier_dict)
        best_classifiers = choose_best_ensemble(all_predictions_dict, self.modeling_dict)
        
        #Handle cases where there's a single classifier chosen
        if type(best_classifiers['classifier_combination']) == str:
            
            single_class = best_classifiers['classifier_combination']
            self.classifiers = {single_class: classifier_dict[single_class]}
            
        else:
            
            self.classifiers = dict((k, classifier_dict[k]) for k in best_classifiers['classifier_combination'])
            
        self.best_acc = best_classifiers['best_acc']
        self.acc_over_most_common = self.best_acc - self.baseline_accuracy
        print 'classifiers used:', self.classifiers.keys()
        print 'best accuracy:', self.best_acc
        print "Accuracy above guessing most common:", self.acc_over_most_common
        
        #Log it
        self.method_history.append('ran_classifiers')
    
    def predict(self, new_data):
        '''runs best ensemble'''
        pred_dict = {}
        
        #Make predictions based for each classifier
        for classifier in self.classifiers.keys():

            # Make predictions on new data
            pred_dict[classifier] = self.classifier[classifier].predict(new_data)
            
        #Vote based on the predictions
        return ensemble_voting(pred_dict)
    
    def prepare_for_pickle(self):
        '''Delete all the data (before serializing the object)'''
        
        del(self.data)
        del(self.modeling_dict)
        del(self.cur)
        self.method_history.append('deleted all data and cursor')
        
    def del_cur(self):
        del(self.cur)