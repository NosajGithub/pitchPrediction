library(ggplot2)
library(pitchRx)
library(dplyr)
library(plyr)
library(DBI)
setwd("~/Desktop/Data Projects/Baseball")

######################################################
##                      Setup                       ##
######################################################

# db <- src_sqlite("new-db.sqlite3", create = TRUE)
# scrape(start = "2008-01-01", end = Sys.Date(), connect = db$c)

db.file <- "new-db.sqlite3"
stopifnot(file.exists(db.file))
db <- src_sqlite(db.file)
# update_db(db$con)

# dbSendQuery(db$con, 'CREATE INDEX pitcher_idx ON atbat(pitcher_name)')
# dbSendQuery(db$con, 'CREATE INDEX pitch_idx ON pitch(gameday_link, num)')

#dbDisconnect(db$con)

atbats <- tbl(db, 'atbat') %>%
        filter(pitcher_name == 'Justin Verlander') %>%
        select(num, gameday_link, stand, batter_name, pitcher_name, event, atbat_des)

pitches <- tbl(db, 'pitch') %>%
        select(des, id, type, tfs_zulu, x, y, sv_id, start_speed, end_speed, sz_top, sz_bot, pfx_x, pfx_z, px, pz, 
               x0, y0, z0, vx0, vy0, vz0, ax, ay, az, break_y, break_angle, break_length, pitch_type, type_confidence, 
               zone, nasty, spin_dir, spin_rate, inning_side, inning, next_, num, on_1b, on_2b, on_3b, gameday_link, count)

verlander <- collect(inner_join(pitches, atbats, by = c('num', 'gameday_link')))
verlander <- arrange(verlander, gameday_link, id)


# dbSendQuery(db$con, 'CREATE INDEX gameday_link_idx ON atbat(gameday_link)')

verlander_games <- tbl(db, 'atbat') %>%
        filter(pitcher_name == 'Justin Verlander') %>%
        select(gameday_link) %>%
        distinct()

all_atbats <- tbl(db,'atbat') %>%
        select(score, home_team_runs, away_team_runs, num, gameday_link)
               #, event, inning_side, start_tfs_zulu, atbat_des, batter_name, pitcher_name)

full_atbats <- collect(inner_join(all_atbats, verlander_games, by = c('gameday_link')))
full_atbats <- arrange(full_atbats,gameday_link, num)
full_atbats$num <- full_atbats$num + 1 # Tricky! Reason is that the score is at that at the end of the at bat, 
                                       # which is relevant for the next atbat

######################################################
##                  Variable Creation               ##
######################################################
verlander$year <- substr(verlander$gameday_link,5,8)
# table(verlander$year,verlander$pitch_type)

# ggplot(verlander, aes(year)) + geom_bar() + facet_wrap(~ pitch_type) #throw out 2008

## Balls and Strikes
verlander$balls <- as.integer(substr(verlander$count,1,1))
verlander$strikes <- as.integer(substr(verlander$count,3,3))

## Runners
verlander$runners <- ""
verlander[is.na(verlander$on_1b) & is.na(verlander$on_2b) & is.na(verlander$on_3b),]$runners <- "empty" 
verlander[!is.na(verlander$on_1b) & is.na(verlander$on_2b) & is.na(verlander$on_3b),]$runners <- "1b"
verlander[is.na(verlander$on_1b) & !is.na(verlander$on_2b) & is.na(verlander$on_3b),]$runners <- "2b"
verlander[is.na(verlander$on_1b) & is.na(verlander$on_2b) & !is.na(verlander$on_3b),]$runners <- "3b"
verlander[!is.na(verlander$on_1b) & !is.na(verlander$on_2b) & is.na(verlander$on_3b),]$runners <- "1b2b"
verlander[!is.na(verlander$on_1b) & is.na(verlander$on_2b) & !is.na(verlander$on_3b),]$runners <- "1b3b"
verlander[is.na(verlander$on_1b) & !is.na(verlander$on_2b) & !is.na(verlander$on_3b),]$runners <- "2b3b"
verlander[!is.na(verlander$on_1b) & !is.na(verlander$on_2b) & !is.na(verlander$on_3b),]$runners <- "loaded"

## Pitch Count
verlander <- arrange(verlander,gameday_link,id)
verlander <- ddply(verlander, .(gameday_link), transform, pitch_count = seq_along(gameday_link))



## Score Differential
full_atbats[is.na(full_atbats$score),]$score <- F
home <- 0
away <- 0
gamel <- full_atbats$gameday_link[1]
for (i in 1:length(full_atbats$num)){
        if (full_atbats$gameday_link[i] != gamel){
                home <- 0
                away <- 0
                gamel <- full_atbats$gameday_link[i]
        }
        if (full_atbats$score[i] == "T"){
                home <- full_atbats$home_team_runs[i]
                away <- full_atbats$away_team_runs[i]
        } else{
                full_atbats$home_team_runs[i] <- home
                full_atbats$away_team_runs[i] <- away
        }
}
rm(home,away,gamel,i)

verlander2 <- merge(full_atbats, verlander, by=c("gameday_link","num"), all.y=TRUE,)
verlander2 <- arrange(verlander2, gameday_link, num, pitch_count)

verlander2$scorediff <- ""
verlander2[verlander2$inning_side == "top","scorediff"] <- as.integer(verlander2[verlander2$inning_side == "top","home_team_runs"]) - 
                                                           as.integer(verlander2[verlander2$inning_side == "top","away_team_runs"])

verlander2[verlander2$inning_side == "bottom","scorediff"] <- as.integer(verlander2[verlander2$inning_side == "bottom","away_team_runs"]) - 
                                                              as.integer(verlander2[verlander2$inning_side == "bottom","home_team_runs"])
verlander2[verlander2$num == 1,]$scorediff <- 0

# temp <- verlander2[verlander2$gameday_link == verlander2$gameday_link[100], 
#                    c("num", "score","home_team_runs","away_team_runs","scorediff","atbat_des",
#                      "pitch_count","batter_name","pitcher_name","inning_side")]


## Normal and Shrunk Pitcher-Batter Priors
## verlander2 <- verlander2[1:5000,] ## TEMP - 3.5 hours for full Verlander sample

# First, create global ids (unique per each pitch, in order)
verlander2 <- arrange(verlander2, gameday_link, num)
verlander2$global_id <- seq_along(verlander2$gameday_link)

# Then, create holders for proportions for the batter and overall
unique_pitches <- paste0(unique(verlander2$pitch_type)) #paste0 for NAs
global_pitch_counter <- as.data.frame(matrix(data=rep(0,length(unique_pitches)),1,length(unique_pitches),
                          dimnames = list("",unique_pitches)))
global_pitch_counter$total <- 0

batter_pitch_counter <- as.data.frame(matrix(data=rep(0,length(unique_pitches)),1,length(unique_pitches),
                                             dimnames = list("",unique_pitches)))
batter_pitch_counter$total <- 0

# Create columns to hold the final tallies for each pitch
verlander2 <- cbind(verlander2, global_pitch_counter) 
global_pitch_counter2 <- global_pitch_counter

colnames(global_pitch_counter2) <- paste0(colnames(global_pitch_counter),"_b")
verlander2 <- cbind(verlander2, global_pitch_counter2)
rm(global_pitch_counter2)

# Loop through pitches to determine per-pitch proportions
# Takes a few minutes

count_pitch_types <- length(names(batter_pitch_counter))

ptm <- proc.time()

for (i in 2:length(verlander2$gameday_link)){
        batter_pitch_counter[1,] <- 0

        ## Load prior pitches into the batter-specific tracker
        for (j in 1:(i-1)){
                if(verlander2$batter_name[i] == verlander2$batter_name[j]){
                        the_pitch_type <- paste0(verlander2$pitch_type[j])
                        batter_pitch_counter[1,the_pitch_type] <- batter_pitch_counter[1,the_pitch_type] + 1
                        batter_pitch_counter$total <- batter_pitch_counter$total + 1
                }
        }
        ## Input batter tracker
        for (k in 1:count_pitch_types){
                verlander2[i,paste0(names(batter_pitch_counter)[k],"_b")] <- batter_pitch_counter[1,k]
        }
        
        ## Input global tracker from prior row (ith = i-1 count + 1 if i-1 pitch was of type)
        for (l in 1:count_pitch_types){

                the_pitch_type <- names(global_pitch_counter)[l]
                
                if (paste0(verlander2$pitch_type[i-1]) != the_pitch_type){
                        verlander2[i,the_pitch_type] <- verlander2[i-1,the_pitch_type]
                } else {
                        verlander2[i,the_pitch_type] <- verlander2[i-1,the_pitch_type] + 1
                }
        }
        verlander2[i,"total"] <- verlander2[i-1,"total"] + 1
}

proc.time() - ptm

## Compute batter and global priors
beta <- 4
n <- verlander2[,"total_b"]
for (k in 1:(count_pitch_types - 1)){ #no total
        the_pitch_type <- names(batter_pitch_counter)[k]
        s <- verlander2[,paste0(the_pitch_type,"_b")] / verlander2[,"total_b"]
        p <- verlander2[,the_pitch_type] / verlander2[,"total"]
        
        verlander2[,paste0("BP_",the_pitch_type)] <- s
        verlander2[,paste0("BP_S_",the_pitch_type)] <- (n * s + beta * p) / (n + beta)
}

a <- cbind(verlander2[,c("batter_name","num","pitch_type")],verlander2[,57:91])

## Pitches so far in the season
verlander2 <- arrange(verlander2,year,gameday_link,id)
verlander2 <- ddply(verlander2, .(year), transform, season_pitch_count = seq_along(gameday_link))

## Times faced that batter already this game
verlander2 <- within(verlander2, {times_faced <- ave(num, list(gameday_link,batter_name), 
                                                FUN=function(x) as.numeric(factor(x,levels=unique(x))))
                                  })
verlander2 <- arrange(verlander2, gameday_link, num, pitch_count)
             
## Count-pitcher prior
unique_counts <- paste0(unique(verlander2$count)) #paste0 for NAs

count_counter <- as.data.frame(row.names = unique_counts,matrix(nrow = length(unique_counts), 
                                                               ncol = length(colnames(batter_pitch_counter)))) 
colnames(count_counter) <- colnames(batter_pitch_counter)
count_counter[,] <- 0

global_pitch_counter_count <- global_pitch_counter
colnames(global_pitch_counter_count) <- paste0(colnames(global_pitch_counter),"_count")
verlander2 <- cbind(verlander2, global_pitch_counter_count)

#For each pitch
#Copy in existing each pitch ratio
#Add one to pitch total and overall total for that count

#Compute CP Priors


if(verlander2$batter_name[i] == verlander2$batter_name[j]){
        the_pitch_type <- paste0(verlander2$pitch_type[j])
        batter_pitch_counter[1,the_pitch_type] <- batter_pitch_counter[1,the_pitch_type] + 1
        batter_pitch_counter$total <- batter_pitch_counter$total + 1
}


## Prior Three pitches

#-----------------------------------------------------
count prior
previous pitches

Try out SVM!
        Reclassify pitches / combine fastballs

Add in other features?
        catcher
        Fan Graphs PitchFx pitch type


---
pitch_type 
stand, balls, strikes, count, inning, inning_side, base_situation(1b,2b,3b), pitches_thrown, score_diff, 
batter-pitcher prior / shrunk prior
pitches so far in the season
number of times batter already faced

count-pitcher prior / shrunk prior
prev2_pitch_type, prev2_velocity, prev2_vert, prev2_hor, prev2_result
prev3_pitch_type, prev3_velocity, prev3_vert, prev3_hor, prev3_result

PitchFx: catcher
FanGraphs: pitch value / batter percentage of pitches faced data
wind / temperature / time of game start (day or night) / umpire

weatherData: humidity data 
