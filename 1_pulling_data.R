# File Name: 1_pulling_data.R
# Purpose: Get the data for a given pitcher

SetUpDb <- function(){
        db <- src_sqlite("new-db.sqlite3", create = TRUE)
        scrape(start = "2008-01-01", end = Sys.Date(), connect = db$c)
        
        # not sure if this scrape is needed or if we can just add players.xml to the scrape above
        scrape(start = '2008-01-01', end = Sys.Date(), suffix = "players.xml", connect = db$c)
        
        dbSendQuery(db$con, 'CREATE INDEX pitcher_idx ON atbat(pitcher_name)')
        dbSendQuery(db$con, 'CREATE INDEX pitch_idx ON pitch(gameday_link, num)')
        dbSendQuery(db$con, 'CREATE INDEX gameday_link_idx ON atbat(gameday_link)')
        dbSendQuery(db$con, 'CREATE INDEX position_idx ON player(current_position)')
}

UpdateDb <- function(){
        db.file <- "new-db.sqlite3"
        stopifnot(file.exists(db.file))
        db <- src_sqlite(db.file)
        update_db(db$con)
        dbDisconnect(db$con)
}

PullData_Pitches <- function(selected_pitcher = 'Justin Verlander', db){
        atbats <- tbl(db, 'atbat') %>%
                filter(pitcher_name == selected_pitcher) %>%
                select(num, gameday_link, stand, batter_name, pitcher_name, event, atbat_des)
        
        pitches <- tbl(db, 'pitch') %>%
                select(des, id, type, tfs_zulu, x, y, sv_id, start_speed, end_speed, sz_top, sz_bot, pfx_x, pfx_z, px, pz, 
                       x0, y0, z0, vx0, vy0, vz0, ax, ay, az, break_y, break_angle, break_length, pitch_type, type_confidence, 
                       zone, nasty, spin_dir, spin_rate, inning_side, inning, next_, num, on_1b, on_2b, on_3b, gameday_link, count)
        
        pdata <- collect(inner_join(pitches, atbats, by = c('num', 'gameday_link')))
        pdata <- arrange(pdata, gameday_link, id)
        pdata
}
 
PullData_AtBats <- function(selected_pitcher = 'Justin Verlander', db){
        selected_pitcher_games <- tbl(db, 'atbat') %>%
                filter(pitcher_name == selected_pitcher) %>%
                select(gameday_link) %>%
                distinct()
        
        all_atbats <- tbl(db,'atbat') %>%
                select(score, home_team_runs, away_team_runs, num, gameday_link)
        
        full_atbats <- collect(inner_join(all_atbats, selected_pitcher_games, by = c('gameday_link')))
        full_atbats <- arrange(full_atbats,gameday_link, num)
        full_atbats$num <- full_atbats$num + 1 # Tricky! Reason is that the score is at that at the end of the at bat, 
                                               # which is relevant for the next atbat
        full_atbats
}

PullData_Catchers <- function(db) {
        catchers <- tbl(db, 'player') %>%
                filter(current_position == 'C') %>%
                select(gameday_link,boxname)
        catchers
}


