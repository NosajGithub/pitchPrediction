###This script saves the Jason Verlander data to a csv, so that it can be read into Python###
personal_path <- '~/Data_Science/final_project/'
setwd(paste(personal_path, 'pitchPrediction/orig_R_code/', sep = ''))

library(dplyr)

load('verlander data.RData')

write.csv(verlander2, '../data/input/sample data/verlander2.csv', row.names = F)