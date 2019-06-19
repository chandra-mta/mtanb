import pandas as pd
import numpy as np
import Chandra.Time 
from kadi import events
from datetime import datetime, timedelta, time

import tensorflow as tf
from tensorflow import keras

# this is a generalized function to take the time that's given by ska
# and format is as datetime
def tme(x):
    return (datetime.strptime(Chandra.Time.DateTime(x).date, '%Y:%j:%H:%M:%S.%f'))
change_time = np.vectorize(tme)

import itertools 
import timeit

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

#reshape the data into time arrays so it looks like [val(t-n), pitch(t-n), roll(t-n),..., val(t), pitch(t)]
#we can choose and play around with n
#https://machinelearningmastery.com/convert-time-series-supervised-learning-problem-python/
#assumes order by time
def reshape_to_multi_time(data, frames=1):
    col_names = data.columns.values
    #df = pd.DataFrame(data)
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
    return agg_full

def shaping_data(scaled_df, pos, frames):
    #reshapes data for an lstm  
    dat = reshape_to_multi_time(scaled_df, frames=frames)
    first_valid_index = dat.first_valid_index()
    #we drop these values since we're not predicting them 
    drop_pos = [id + "(t)" for id in pos]
    shaped = dat.drop(drop_pos, axis = 1).values
    return (shaped, first_valid_index)

#data should already be shaped for an lstm-type network
def split_data_for_model(msid_data, time_data, time_offset, split, first_split, last_split):
    chunk = int(msid_data.shape[0]/split)
    # here we split the data into training, validation and test 
    train_data    = msid_data[ :chunk * first_split                        , :]
    validate_data = msid_data[ chunk * first_split:chunk * last_split      , :]
    test_data     = msid_data[ chunk * last_split:                         , :]
    #here we split the time to correspond
    train_time    = time_data[ time_offset:chunk * first_split + time_offset]
    validate_time = time_data[ time_offset + chunk*first_split : time_offset + chunk*last_split ]
    test_time     = time_data[ time_offset + chunk*last_split  : ]
    if (train_data.shape[0] != train_time.shape[0] 
        or validate_data.shape[0] != validate_time.shape[0]
        or test_data.shape[0] != test_time.shape[0]):
        print ("shape discrepancy! time offset: ", time_offset)
        print (train_data.shape, train_time.shape)
        print (validate_data.shape, validate_time.shape)
        print (test_data.shape, test_time.shape)
    return (train_data, validate_data, test_data, train_time, validate_time,  test_time)

def split_io(interval, frames, n_features):
    #split into inputs and outputs
    interval_X, interval_y = interval[:, :-1], interval[:, -1]
    #reshape input to be 3D tensor with shape (samples, timesteps, features]
    interval_X = interval_X.reshape((interval_X.shape[0], frames, n_features))
    return (interval_X, interval_y)