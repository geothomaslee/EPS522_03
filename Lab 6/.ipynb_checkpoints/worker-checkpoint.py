def worker(dataset, lat):
    lon = -105
    timeseries=dataset['sst'][:,lat,lon]
    print(timeseries[0])