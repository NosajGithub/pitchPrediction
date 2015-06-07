###Functions to Help Explore the Pitch Data###
def get_pitch_types_by_year(pitcher_data, date_col = None, use_gameday = True):
    '''Given DF for a single pitcher, returns a DF of their pitch type counts by year
    
    pitcher_data: DF of pitch data for a single pitcher
    date_col: if present, the string name of the column that contains the date on which the pitch was thrown
    use_gameday: whether or not the gameday_link column should be used to derive the date'''
    
    #extract the date from the gameday_id, if necessary
    if use_gameday:
        pitcher_data['date'] = pitcher_data['gameday_link'].str.slice(start = 4, stop = 14)
        pitcher_data['date'] = pitcher_data['date'].str.replace("_", "-")
        pitcher_data['date'] = pd.to_datetime(pitcher_data['date'])
        
    #Check for date col and reassign
    if date_col is not None:
        pitcher['date'] = pitcher[date_col]
    
    #Index on the date and aggregate to the year (season) level
    pitcher_data = pitcher_data.set_index('date')
    pitcher_data = pitcher_data.groupby([lambda x: x.year, 'pitch_type']).size()
    
    #Unstack the data so each pitch type can be plotted
    unstacked = pitcher_data.unstack()
    return unstacked

def plot_pitch_types(pitcher_data, pitcher_name = 'unspecified'):
    '''Thus function takes in pitcher data (like the verlander sample), and creates a plot of pitch types over time.
    Variable descriptions:
    
    pitcher_data: Pandas DF for a single pitcher
    pitcher_name: Name of the pitcher's data being passed into the function'''

    #plot
    pitcher_data.plot(title = 'Pitches over time for ' + pitcher_name)