#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 10:30:26 2023

@author: thomaslee
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import netCDF4 as nc
import datetime
import scipy.optimize
import time
from multiprocessing import Pool

dataset = nc.Dataset('../../../sst.mon.mean.nc')

#startyear is 1890

import scipy 

def fit_line_slope(xdata, ydata):
    def linear_func(x, a, b):
        return a*x + b
    
    fit, uncertainty = scipy.optimize.curve_fit(f = linear_func,
                                                xdata = xdata,
                                                ydata = ydata)
    slope = fit[0]
    y_int = fit[1]
    
    return slope, y_int

def get_decimal_years(startyear,months):
    times_list = []
    
    months_list = np.arange(0, months, 1)
    for mon in months_list:
        cur_time = 1890 + (mon / 12)
        times_list.append(cur_time)
        
    times_array = np.array(times_list)
    
    return times_array

# Testing how these functions work over a single location
testlat = 35
testlon = -140
testlon_2 = -105
test_data = dataset['sst'][:,testlat,testlon]
test_data_2 = dataset['sst'][:,testlat,testlon_2]

# Times will be used later
times = get_decimal_years(1890, 1590)

fit_slope, y_int = fit_line_slope(times, test_data)
fit_y = (times * fit_slope) + y_int

plt.plot(times, test_data)
plt.plot(times, fit_y)
plt.show()

lats = np.arange(-90, 90, 1)
lons = [-130, -129, -128]

"""
# Method 1
This is some testing I did to test if it would be faster to fix the longitude and only call part of the file every time.
The answer is a DEFINITIVE yes. Method 1 takes 4 seconds to run through 3 longitudes and every latitude, Method 2 takes
more like 800 seconds or so. 

test_time = time.perf_counter()

for lon in lons:
        dataset_fixed_lon = dataset['sst'][:,:,lon]
        print(f'Working on Lon {lon}')
        for lat in lats:
            timeseries = dataset_fixed_lon[:,lat]
            print(timeseries[0])

end_time = time.perf_counter()
print(f'Method 1 time: {end_time - test_time}')
"""

test_2_time = time.perf_counter()

if __name__ == '__main__':
    with Pool() as pool:
        for lon in lons:
            for lat in lats:
                if dataset['sst'][0,lat,lon].mask:
                    print(f'Lon {lon} Lat {lat} is continent!')
                else:
                    timeseries = dataset['sst'][:,lat,lon]
                    fit_slope, y_int = fit_line_slope(times, timeseries)
                    print(fit_slope)
    
print(f'Calculation time: {time.perf_counter() - test_2_time}')





