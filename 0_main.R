# File Name: 0_main.R
# Purpose: The main program that runs the whole process for a given pitcher

# setwd("~/Desktop/Data Projects/Baseball/pitchPrediction/")

library(pitchRx)
library(ggplot2)
library(pitchRx)
library(dplyr)
library(plyr)
library(DBI)

source("1_pulling_data.R")
source("2_adding_variables.R")
source("3_predictions.R")

# Pull data from database
db <- src_sqlite("new-db.sqlite3")
pdata <- PullData_Pitches(selected_pitcher = 'Justin Verlander', db = db)
full_atbats <- PullData_AtBats(selected_pitcher = 'Justin Verlander', db = db)

# Add variables
pdata <- Make_year(pdata)
pdata <- Make_balls_strikes(pdata)
pdata <- Make_runners(pdata)
pdata <- Make_pitch_count(pdata)
pdata <- Make_score_differential(pdata, full_atbats)
#pdata <- Make_pitcher_batter_priors(pdata) # Warning: Takes hours for large numbers of pitches
                                            # With x rows, it takes about ((.0025*x + .0000165*(x^2))/60) minutes
pdata <- Make_pitcher_count_priors(pdata)
pdata <- Make_season_pitches(pdata)
pdata <- Make_times_faced(pdata)



