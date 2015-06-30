# TODO: Maximum Entropy Binning
def max_entropy_binning():
    pass

# Feature transformations
# TODO: Log Transform
# TODO: Power Transform

# Standardization (One-hot encoding and hashing trick)
# TODO: Fix Missing Values

def men_on_feature(df):

    """Given a pandas dataframe containing all pitches for a single pitcher, 
    returns a dataframe with four features: men on first/second/third for that particular pitch (1 = man on that base, 0 = no man on that base),
    and also total men on during that pitch 
    Uses pitch table columns: on_1b, on_2b, on_3b
    """

    onfirst = pitcher_sample_df['on_1b']
    onsecond = pitcher_sample_df['on_2b']
    onthird = pitcher_sample_df['on_3b']

    basearray = []

    for i in range(0, pitcher_sample_df.shape[0]):
        total = 0
        if onfirst[i] > 0:
            who = 1
        else:
            who = 0
        if onsecond[i] > 0:
            what = 1
        else:
            what = 0
        if onthird[i] > 0:
            idontknow = 1
        else:
            idontknow = 0
        total = who + what + idontknow
        basearray.append([who, what, idontknow, total])

    rdf = pd.DataFrame(basearray, columns = ['1b', '2b', '3b', 'totb']) # make dataframe with columns for each base + total bases
    return rdf