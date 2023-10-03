import scipy
import numpy as np
import glob
import pandas as pd
import scipy.stats as stats

def fit_timeseries(tlist, ylist):
    """
    Parameters
    ----------
    tlist: np.array of the times for the time series, as a decimal year
    ylist: np.array of the displacement timeseries y-values
    
    Returns least_squares_velocity and uncertainty

    -------
    Notes
    """
    def linear_func(x, a, b):
        return a*x + b

    least_squares_velocity, uncertainty = scipy.optimize.curve_fit(f = linear_func,
                                                                   xdata = tlist,
                                                                   ydata = ylist)
    
    return least_squares_velocity, uncertainty

def fit_velocities(filename):
    """
    Parameters
    ----------
    filename: string giving the name of the tenv3 GPS file
    
    Returns velocity in m/year and the covariance matrix for each component
    -------
    Notes
    """
    gps_data = pd.read_csv(filename,
                           sep='\s+')
    
    years = gps_data['yyyy.yyyy'].tolist()
    east = gps_data['__east(m)'].tolist()
    north = gps_data['_north(m)'].tolist()
    vert = gps_data['____up(m)'].tolist()
    
    east_velocity, east_uncertainty = fit_timeseries(years, east)
    north_velocity, north_uncertainty = fit_timeseries(years, north)
    vert_velocity, vert_uncertainty = fit_timeseries(years, vert)
    
    return east_velocity[0], east_uncertainty, north_velocity[0], north_uncertainty, vert_velocity[0], vert_uncertainty

def get_coordinates(filename):
    """
    Parameters
    ----------
    filename: string giving the name of the tenv3 GPS file
    
    Returns average longitude, average latitude, and average elevation in meters of the GPS station over the time interval of the file
    -------
    Notes
    """
    gps_data = pd.read_csv(filename,
                           sep='\s+')
    lat = gps_data['_latitude(deg)'].tolist()
    lon = gps_data['_longitude(deg)'].tolist()
    elev = gps_data['__height(m)'].tolist()
    
    lat_avg = sum(lat) / len(lat)
    lon_avg = sum(lon) / len(lat)
    elev_avg = sum(elev) / len(elev)

    return lat_avg, lon_avg, elev_avg

def fit_all_gps_velocities(folder,pattern):
    """
    Parameters
    ----------
    folder : string 
        Gives the name of the folder containig the GPS files
    pattern : string
        glob pattern for naming all the GPS files
    
    Returns a pandas.DataFrame.Dataframe object containing information about each GPS station
    -------
    This function assumes that the folder containing the GPS files is inside of the folder from where this script is run.
    """
    
    filekey = f'./{folder}/{pattern}'
    files = glob.glob(filekey)
    
    site_list = []
    lon_list = []
    lat_list = []
    elev_list = []
    east_vel_list = []
    east_uncer_list = []
    north_vel_list = []
    north_uncer_list = []
    vert_vel_list = []
    vert_uncer_list = []
    
    for file in files:
        gps_data = pd.read_csv(file,
                               sep='\s+')
        
        site_name = gps_data['site'][0]
        lon, lat, elev = get_coordinates(file)
        east_vel, east_uncer, north_vel, north_uncer, vert_vel, vert_uncer = fit_velocities(file)
        
        site_list.append(site_name)
        lon_list.append(lon)
        lat_list.append(lat)
        elev_list.append(elev)
        east_vel_list.append(east_vel)
        east_uncer_list.append(east_uncer)
        north_vel_list.append(north_vel)
        north_uncer_list.append(north_uncer)
        vert_vel_list.append(vert_vel)
        vert_uncer_list.append(vert_uncer)
    
    gps_df = pd.DataFrame(list(zip(site_list, lon_list, lat_list, elev_list, east_vel_list, 
                                   east_uncer_list, north_vel_list, north_uncer_list, vert_vel_list, vert_uncer_list)),
                          columns=['Site', 'Longitude', 'Latitude', 'Elevation', 
                                   'East Velocity (m/s)', 'East Covariance Matrix',
                                   'North Velocity (m/s)', 'North Covariance Matrix',
                                   'Vertical Velocity (m/s)', 'Vertical Covariance Matrix'])
                               
    return gps_df

def fit_tide_gauge(tlist, ylist):
    """
    Parameters
    ----------
    tlist: np.array of the times for the time series, as a decimal year
    ylist: np.array of the tide-gauge timeseries y-values
    
    Returns least_squares_gauge and uncertainty
    -------
    Notes
    """
    def linear_func(x, a, b):
        return a*x + b

    least_squares_velocity, uncertainty = scipy.optimize.curve_fit(f = linear_func,
                                                                   xdata = tlist,
                                                                   ydata = ylist)
    
    return least_squares_velocity, uncertainty

def fit_all_tide_velocities(folder,pattern):
    """
    Parameters
    ----------
    folder : string 
        Gives the name of the folder containig the GPS files
    pattern : string
        glob pattern for naming all the GPS files
    type : string
        Either 'GNSS' or 'Tide'
    
    Returns a pandas.DataFrame.Dataframe object containing information about each tide gauge station
    -------
    This function assumes that the folder containing the tide files is inside of the folder from where this script is run.
    """
    
    filekey = f'./{folder}/{pattern}'
    files = glob.glob(filekey)
    
    tide_vel_list = []
    tide_uncer_list = []
    
    for file in files:
        tide_data = pd.read_csv(file,
                               sep=';',
                               names=['year','mm','idk','also idk'])
        
        # Identifying outliers
        tide_data_mm = tide_data['mm'].to_frame()
        z_scores = stats.zscore(tide_data_mm)
        abs_z_scores = np.abs(z_scores)
        # Replacing outliers with Nan
        filtered_entries = (abs_z_scores < 1).all(axis=1)
        new_tide_data_mm = tide_data_mm[filtered_entries]
        
        # Dropping rows with Nan
        tide_data['mm'] = new_tide_data_mm['mm']
        tide_data = tide_data.dropna()
        
        # Calculating fit
        tide_vel, tide_uncer = fit_tide_gauge(tide_data['year'],tide_data['mm'])
        
        tide_vel_list.append(tide_vel[0])
        tide_uncer_list.append(tide_uncer)
    
    tide_df = pd.DataFrame(list(zip(files, tide_vel_list, tide_uncer_list)),
                          columns=['File','Sea Level Change (mm)','Uncertainty Covariance Matrix'])
                               
    return tide_df

def fit_all_velocities(folder,pattern,type='GNSS'):
    if type == 'GNSS':
        return_df = fit_all_gps_velocities(folder, pattern)
        print('Using this one!')
    elif type == 'Tide':
        return_df = fit_all_tide_velocities(folder, pattern)
    else:
        raise ValueError("Type must be GNSS or Tide")
        
    return return_df
       
