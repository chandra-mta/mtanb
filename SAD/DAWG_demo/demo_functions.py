import numpy as np
import itertools
import timeit
import pandas as pd

#numpy doesn't know how to round float64, so creating a helper function
def round_vals(msid_val, round_dig):
    return (round(float(msid_val), round_dig))
rounded = np.vectorize(round_vals)

########################################
# The purpose of the two functions below is to map the right positional
# arguments to the right timing for the MSID we're looking
# logical_intervals creates intervals of time during which an MSID
# holds a certain value and select_intervals maps these intervals 
# to the times column of the MSID
#######################################

def logical_intervals(times, values):
    i = 0
    ending = len(times)
    intervals = []
    inter_values = []
    # from the itertools documentation:
    # [k for k, g in groupby('AAAABBBCCDAABBB')] --> A B C D A B
    # [list(g) for k, g in groupby('AAAABBBCCD')] --> AAAA BBB CC D
    # itertools.groupby returns A:[A,A,A,A], B:[B,B,B], C:[C,C], D:[D]
    grouped_vals = itertools.groupby(values)
    for loc_value, group in itertools.groupby(values):
        elems = len(list(group))
        begin = times[i] if i > 0 else times[i]-3600.00
        i += elems
        end = times[i] if i < ending else times[i-1]+1000000
        intervals += [(begin, end)]
        inter_values += [loc_value]
    return (intervals, inter_values)

def select_intervals(msid_data, loc_data):
    lstart = timeit.default_timer()
    msid_loc = np.empty(len(msid_data.times))
    round_loc_data = rounded(loc_data.vals, 2)
    print("rounded: ", timeit.default_timer() - lstart)
    intervals, inter_values = logical_intervals(loc_data.times, round_loc_data)
    print("logiced: ", timeit.default_timer()  - lstart)
    #here we are using the intervals from logic_intervals to create a datafram where the intervals are the index
    interval_dataframe = pd.DataFrame(inter_values, index = pd.IntervalIndex.from_tuples(intervals, closed = 'left'),
                                     columns = ['val'])
    #having intervals as the index allows us to do the below functioning
    #we give interval_dataframe a list of times and it returns the value attached to it
    print ("msid_shape: ",  msid_data.times.shape )
    print("interval_shape: ", interval_dataframe.shape)
    msid_loc = interval_dataframe.loc[msid_data.times]
    print("intervaled: ", timeit.default_timer() - lstart)
    return (msid_loc['val'].values)

######################################################
# the following is modified from the Quaternion code to allow for arrays
# Quaternion must already be normalized (which in this script it is)
######################################################
def quat2equatorial(quat_vals):
    """
    Determine right Ascension, Declination, and Roll for the object quaternion
    
    :inputs: 
    :return: RA, Dec, Roll
    :rtype: numpy array [ra,dec,roll]
    """
    q = np.array(quat_vals)
    q2 = q**2
    # calculate direction cosine matrix elements from $quaternions
    xa = q2[:,0] - q2[:,1] - q2[:,2] + q2[:,3]
    xb = 2 * (q[:,0] * q[:,1] + q[:,2] * q[:,3])
    xn = 2 * (q[:,0] * q[:,2] - q[:,1] * q[:,3])
    yn = 2 * (q[:,1] * q[:,2] + q[:,0] * q[:,3])
    zn = q2[:,3] + q2[:,2] - q2[:,0] - q2[:,1]
    # Due to numerical precision this can go negative. Allow *slightly* negative
    # values but raise an exception otherwise
    one_minus_xn2 = 1 - xn**2
    if np.any(one_minus_xn2 < 0):
        if np.any(one_minus_xn2 < -1e-12):
            raise ValueError('Unexpected negative norm: {}'.format(one_minus_xn2))
        one_minus_xn2[one_minus_xn2 < 0 ] = 0
    ra = np.degrees(np.arctan2(xb, xa))
    dec = np.degrees(np.arctan2(xn, np.sqrt(one_minus_xn2)))
    roll = np.degrees(np.arctan2(yn, zn))
    ra_add = np.full(ra.shape[0], 0)
    roll_add = np.full(roll.shape[0],0)
    
    if (np.any(ra < 0)):
        ra_add[(ra < 0)] = 360
        ra = ra + ra_add
    if (np.any(roll < 0)):
        roll_add[(roll < 0)] = 360
        roll = roll + roll_add
    return (np.array([ra, dec, roll]))

#yaw is equal to ra0, which is equal to _get_zero
def get_yaw(ra):
    val = ra%360.0
    val_add = np.full(ra.shape[0],0)
    if (np.any(val >= 180)):
        val_add[(val>= 180)] = 360
        val = val - val_add
    return val

def get_quaternion(quat_vals):
    # returns roll and yaw
    # pitch ise -dec
    equatorial = quat2equatorial(quat_vals)
    ra, dec, roll = equatorial[0], equatorial[1], equatorial[2]
    yaw = get_yaw(ra)
    print (ra.shape, dec.shape, roll.shape, yaw.shape)
    return (np.array([ra, dec, roll, yaw]))

#########################################
from sklearn.preprocessing import MinMaxScaler

def scale_training(train_set, raw_msid_val):
    # normalize data (to be between 0 and 1) and then reshape 
    scaler_full = MinMaxScaler()
    scaled = scaler_full.fit_transform(train_set)
    # creating a seperate scaling for msid_vals cause honestly it's ruining my life
    scaler_msid = MinMaxScaler()
    scaled_msid_val = scaler_msid.fit_transform(raw_msid_val)
    # scaled_df = pd.DataFrame(scaled, columns = raw.columns).iloc[::spacing_int,:]
    scaled_train = pd.DataFrame(scaled, columns = train_set.columns)
    print ("big df shape: ", scaled_train.shape)

    return (scaler_full, scaler_msid, scaled_train)


def get_avg_set(spacing_int, data, var):
    padding_int = spacing_int - (data[var].shape[0]%spacing_int)
    padding = np.empty(padding_int, dtype=np.float32)
    padded_vals = np.concatenate((data[var], padding), axis=0)
    avg_vals = np.mean(padded_vals.reshape(-1,spacing_int), axis=1)[:-1]
    return (avg_vals)

def get_averaged_data(scaled_data, time, spacing_int, variables):
    intrv_times = time[::spacing_int][:-1]
    print ("intv_times shape: ", intrv_times.shape)
    # TODO: change shaping data to take in list of names to go in a dict, create df and shape it 
    intervaled_dict = {}
    for key in variables:
        intervaled_dict[key] = get_avg_set(spacing_int, scaled_data, key)
    intervaled_obs = pd.DataFrame(intervaled_dict)
    return (intervaled_obs, intrv_times)


def clean_data(data, cols, pos):
    #cleaning that needs to occur for all sets(train, validation, test)
    #first take out any null values with a mask
    #return the time data and the msid data (the time data is for plotting)
    subset = data[cols]
    mask = [all(tup) for tup in zip(*[~np.isnan(subset['{}'.format(i)]) for i in pos])]
    masked = subset[mask]
    #seperate out the time data
    msid_times = masked['msid_times']
    raw_times = masked['raw_times']
    raw_set = masked.drop(['msid_times', 'raw_times'], axis = 1)
    return raw_set, raw_times, msid_times

#############################################
#reshape the data into time arrays so it looks like [val(t-n), pitch(t-n), roll(t-n),..., val(t), pitch(t)]
#we can choose and play around with n
#https://machinelearningmastery.com/convert-time-series-supervised-learning-problem-python/
#assumes order by time
def reshape_to_multi_time(data, frames=1):
    col_names = data.columns.values
    cols, names = list(), list()
    #input sequence (t-n, ... t-1)
    for i in range(frames, 0, -1):
        cols.append(data.shift(i))
        names += [('%s(t-%d)' % (name,  i)) for name in col_names]
    #forecast sequence (t, t+1, ... t+n)
    for i in range(0,1):
        cols.append(data.shift(-i))
        if i == 0: 
            names += [('%s(t)' % (name)) for name in col_names]
        else:
            names += [('%s(t+%d)' % (name, i)) for name in col_names]
    #put it all together
    agg = pd.concat(cols, axis = 1)
    agg.columns = names
    #drops rows with NaN values
    agg_full = agg.dropna()
    print (agg_full[:5])
    return agg_full

def shaping_data(scaled_df, pos, frames):
    #reshapes data for an lstm  
    dat = reshape_to_multi_time(scaled_df, frames=frames)
    first_valid_index = dat.first_valid_index()
    #we drop these values since we're not predicting them 
    drop_pos = [id + "(t)" for id in pos]
    shaped = dat.drop(drop_pos, axis = 1).values
    return (shaped, first_valid_index)

def split_shaped_data(shaped_data, time, percentage, offset):
    chunk = int(shaped_data.shape[0]*(1-percentage))
    left_chunk, left_time = shaped_data[:chunk], time[:chunk]
    right_chunk,  right_time = shaped_data[chunk:],  time[chunk+offset:]
    print("chunk_sizes: (left, time, right, time)", left_chunk.shape,left_time.shape, right_chunk.shape, right_time.shape)
    return (left_chunk, left_time, right_chunk, right_time)

def split_io(interval, frames, n_features):
    #split into inputs and outputs
    interval_X, interval_y = interval[:, :-1], interval[:, -1]
    print ("interval 1", interval_X.shape)
    #reshape input to be 3D tensor with shape (samples, timesteps, features]
    interval_X = interval_X.reshape((interval_X.shape[0], frames, n_features))
    print ("interval 2", interval_X.shape)
    return (interval_X, interval_y)