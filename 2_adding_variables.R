# File Name: 2_adding_variables.R
# Purpose: Construct the features used in prediction

Make_year <- function(pdata){
        pdata$year <- substr(pdata$gameday_link,5,8)
        pdata
}

Make_balls_strikes <- function(pdata){
        pdata$balls <- as.integer(substr(pdata$count,1,1))
        pdata$strikes <- as.integer(substr(pdata$count,3,3))
        pdata
}

Make_runners <- function(pdata){
        pdata$runners <- ""
        pdata[is.na(pdata$on_1b) & is.na(pdata$on_2b) & is.na(pdata$on_3b),]$runners <- "empty" 
        pdata[!is.na(pdata$on_1b) & is.na(pdata$on_2b) & is.na(pdata$on_3b),]$runners <- "1b"
        pdata[is.na(pdata$on_1b) & !is.na(pdata$on_2b) & is.na(pdata$on_3b),]$runners <- "2b"
        pdata[is.na(pdata$on_1b) & is.na(pdata$on_2b) & !is.na(pdata$on_3b),]$runners <- "3b"
        pdata[!is.na(pdata$on_1b) & !is.na(pdata$on_2b) & is.na(pdata$on_3b),]$runners <- "1b2b"
        pdata[!is.na(pdata$on_1b) & is.na(pdata$on_2b) & !is.na(pdata$on_3b),]$runners <- "1b3b"
        pdata[is.na(pdata$on_1b) & !is.na(pdata$on_2b) & !is.na(pdata$on_3b),]$runners <- "2b3b"
        pdata[!is.na(pdata$on_1b) & !is.na(pdata$on_2b) & !is.na(pdata$on_3b),]$runners <- "loaded"
        pdata
}

Make_pitch_count <- function(pdata){
        pdata <- arrange(pdata,gameday_link,id)
        pdata <- ddply(pdata, .(gameday_link), transform, pitch_count = seq_along(gameday_link))
        pdata
}

Make_score_differential <- function(pdata,full_atbats){
        # Determine the score at the start of each at bat, merge into pitch table
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
        pdata2 <- merge(full_atbats, pdata, by=c("gameday_link","num"), all.y=TRUE)
        pdata2 <- arrange(pdata2, gameday_link, num, pitch_count)
        
        pdata2$scorediff <- ""
        pdata2[pdata2$inning_side == "top","scorediff"] <- as.integer(pdata2[pdata2$inning_side == "top","home_team_runs"]) - 
                as.integer(pdata2[pdata2$inning_side == "top","away_team_runs"])
        
        pdata2[pdata2$inning_side == "bottom","scorediff"] <- as.integer(pdata2[pdata2$inning_side == "bottom","away_team_runs"]) - 
                as.integer(pdata2[pdata2$inning_side == "bottom","home_team_runs"])
        pdata2[pdata2$num == 1,]$scorediff <- 0        
        pdata2
}

Make_pitcher_batter_priors <- function(pdata){
        # First, create global ids (unique per each pitch, in order)
        pdata <- arrange(pdata, gameday_link, num)
        pdata$global_id <- seq_along(pdata$gameday_link)
        
        # Then, create holders for proportions for the batter and overall
        unique_pitches <- paste0(unique(pdata$pitch_type)) #paste0 for NAs
        global_pitch_counter <- as.data.frame(matrix(data=rep(0,length(unique_pitches)),1,length(unique_pitches),
                                                     dimnames = list("",unique_pitches)))
        global_pitch_counter$total <- 0
        
        batter_pitch_counter <- as.data.frame(matrix(data=rep(0,length(unique_pitches)),1,length(unique_pitches),
                                                     dimnames = list("",unique_pitches)))
        batter_pitch_counter$total <- 0
        
        # Create columns to hold the final tallies for each pitch
        pdata <- cbind(pdata, global_pitch_counter) 
        global_pitch_counter2 <- global_pitch_counter
        
        colnames(global_pitch_counter2) <- paste0(colnames(global_pitch_counter),"_b")
        pdata <- cbind(pdata, global_pitch_counter2)
        rm(global_pitch_counter2)
        
        # Loop through pitches to determine per-pitch proportions
        # Takes a few minutes
        
        count_pitch_types <- length(names(batter_pitch_counter))
        
        ptm <- proc.time()
        
        for (i in 2:length(pdata$gameday_link)){
                batter_pitch_counter[1,] <- 0
                
                ## Load prior pitches into the batter-specific tracker
                for (j in 1:(i-1)){
                        if(pdata$batter_name[i] == pdata$batter_name[j]){
                                the_pitch_type <- paste0(pdata$pitch_type[j])
                                batter_pitch_counter[1,the_pitch_type] <- batter_pitch_counter[1,the_pitch_type] + 1
                                batter_pitch_counter$total <- batter_pitch_counter$total + 1
                        }
                }
                ## Input batter tracker
                for (k in 1:count_pitch_types){
                        pdata[i,paste0(names(batter_pitch_counter)[k],"_b")] <- batter_pitch_counter[1,k]
                }
                
                ## Input global tracker from prior row (ith = i-1 count + 1 if i-1 pitch was of type)
                for (l in 1:count_pitch_types){
                        
                        the_pitch_type <- names(global_pitch_counter)[l]
                        
                        if (paste0(pdata$pitch_type[i-1]) != the_pitch_type){
                                pdata[i,the_pitch_type] <- pdata[i-1,the_pitch_type]
                        } else {
                                pdata[i,the_pitch_type] <- pdata[i-1,the_pitch_type] + 1
                        }
                }
                pdata[i,"total"] <- pdata[i-1,"total"] + 1
        }
        
        proc.time() - ptm
        
        ## Compute batter and global priors
        beta <- 4
        n <- pdata[,"total_b"]
        for (k in 1:(count_pitch_types - 1)){ #no total
                the_pitch_type <- names(batter_pitch_counter)[k]
                s <- pdata[,paste0(the_pitch_type,"_b")] / pdata[,"total_b"]
                p <- pdata[,the_pitch_type] / pdata[,"total"]
                
                pdata[,paste0("BP_",the_pitch_type)] <- s
                pdata[,paste0("BP_S_",the_pitch_type)] <- (n * s + beta * p) / (n + beta)
        }

        pdata[, -which(names(pdata) %in% c(paste0(unique_pitches),paste0(unique_pitches,"_b"),"total","total_b")]
        
        unique_pitches_v <- paste0(unique(verlander2$pitch_type)) #paste0 for NAs
}

Make_season_pitches <- function(pdata) {
        ## Pitches so far in the season
        pdata <- arrange(pdata,year,gameday_link,id)
        pdata <- ddply(pdata, .(year), transform, season_pitch_count = seq_along(gameday_link))
        pdata
}

Make_times_faced <- function(pdata){
        ## Times faced that batter already this game
        pdata <- within(pdata, {times_faced <- ave(num, list(gameday_link,batter_name), 
                                                   FUN=function(x) as.numeric(factor(x,levels=unique(x))))
        })
        pdata <- arrange(pdata, gameday_link, num, pitch_count)
        pdata
}

Make_pitcher_count_priors <- function(pdata){
        # Make global store of counts of pitches in different pitch counts 
        unique_pitches <- c(paste0(unique(pdata$pitch_type)),"total") #paste0 for NAs
        unique_counts <- paste0(unique(pdata$count)) #paste0 for NAs
        count_counter <- as.data.frame(row.names = unique_counts,matrix(nrow = length(unique_counts), 
                                                                        ncol = length(unique_pitches))) 
        colnames(count_counter) <- unique_pitches
        count_counter[,] <- 0
        
        # Add in rows to receive counts of pitches in different pitch counts
        global_pitch_counter <- as.data.frame(matrix(data=rep(0,length(unique_pitches)),1,length(unique_pitches),
                                                     dimnames = list("",paste0(unique_pitches,"_count"))))
        pdata <- cbind(pdata, global_pitch_counter)
        
        # For each pitch, copy in existing each pitch ratio, then add one to pitch total and overall total for that count
        count_pitch_types <- length(unique_pitches)
        for (i in 1:length(pdata$gameday_link)){                
                the_count <- paste0(pdata[i,"count"])
                for (k in 1:count_pitch_types){
                        the_pitch <- unique_pitches[k]
                        pdata[i,paste0(the_pitch,"_count")] <- count_counter[the_count,paste0(the_pitch)]
                }
                count_counter[the_count,paste0(pdata[i,"pitch_type"])] <- count_counter[the_count,paste0(pdata[i,"pitch_type"])] + 1
                count_counter[the_count,"total"] <- count_counter[the_count,"total"] + 1
        }
        
        #Compute CP Priors
        for (k in 1:(count_pitch_types - 1)){ #no total
                the_pitch_type <- unique_pitches[k]
                pdata[,paste0("PC_",the_pitch_type)] <- pdata[,paste0(the_pitch_type,"_count")] / pdata[,"total_count"]
        }        
        pdata[, -which(names(pdata) %in% paste0(unique_pitches,"_count"))]
}


