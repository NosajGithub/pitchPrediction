CREATE TABLE all_pitch_data as
SELECT
	p.*,
	ab.half,
	ab.inning,
	ab.o, /*Note: This is a leak from the future. Need to fix!*/
	ab.score,	/*Note: This could be a leak from the future. Need to fix!*/
	ab.stand,
	ab.b_height,
	ab.p_throws,
	ab.event, /*Known leak from future BUT could be used as feature if we lag it...*/
	ab.event2, /*Known leak from future BUT could be used as feature if we lag it...*/
	ab.event3, /*Known leak from future BUT could be used as feature if we lag it...*/
	ab.home_team_runs, /*leak from future*/
	ab.away_team_runs, /*leak from future*/
	pitchers.first_name as p_first_name,
	pitchers.last_name as p_last_name,
	pitchers.height as p_height,
	pitchers.dob as pitcher_dob,
	batters.first_name as b_first_name,
	batters.last_name as b_last_name,
	batters.dob as batter_dob,
	gm.game_type,
	gm.local_game_time,
	gm.game_pk, /*Don't know what this means*/
	gm.game_time_et,
	gm.home_id, /*don't know if this is necessary since we know home_fname*/
	gm.home_fname,
	gm.home_wins, /*Not sure if this is a leak from the future or not. prob not a problem*/
	gm.home_loss, /*Not sure if this is a leak from the future or not. prob not a problem*/
	gm.away_id,
	gm.away_fname,
	gm.away_wins,
	gm.away_loss,
	gm.status_ind,
	gm.date,
	gm.day,
	gm.stadium_name
	/*Note: I left out some variables like gm.stadium_id that didn't seem necessary for us*/
FROM
	pitch p
	LEFT JOIN
		atbat ab ON p.game_id = ab.game_id AND p.num = ab.num
	LEFT JOIN
		player pitchers ON pitchers.id = p.pitcher
	LEFT JOIN
		player batters ON batters.id = p.batter	
	LEFT JOIN
		game gm ON gm.game_id = p.game_id;