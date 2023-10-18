def worker(dataset):
    lon = -105
    for lat in lats:
            timeseries=dataset['sst'][:,lat,lon]
            print(timeseries[0])