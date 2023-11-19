import scipy
import numpy as np
import glob
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt


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

def fit_all_tide_velocities(folder,pattern, outlier_thresh=3):
    """
    Parameters
    ----------
    folder : string 
        Gives the name of the folder containig the GPS files
    pattern : string
        glob pattern for naming all the GPS files
    outlier_thresh : int or float
        Z-score above which data is called an outlier and will be thrown out
    
    Returns : pandas.DataFrame.DataFrame
        Data frame containing information about each tide gauge station
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
        filtered_entries = (abs_z_scores < outlier_thresh).all(axis=1)
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

def fit_all_velocities(folder,pattern,type='GNSS',outlier_thresh=3):
    """
    Parameters
    ----------
    folder : string
        name or path of folder
    pattern : string
        glob pattern for file names
    type : string
        'GNSS' or 'Tide'
    outlier_thresh : int or float
        Z-score above which data will be thrown out from tide data
    ----------    
    Returns : return_df
        The data frame from the fitting function of the selected data type
    """
        
    if type == 'GNSS':
        if outlier_thresh != None:
            print('Note: Cannot remove outliers from GPS Data')
        return_df = fit_all_gps_velocities(folder, pattern)
    elif type == 'Tide':
        return_df = fit_all_tide_velocities(folder, pattern,outlier_thresh)
    else:
        raise ValueError("Type must be GNSS or Tide")
        
    return return_df
       
def plot_velocities (gps_df, east_vel_list, north_vel_list, vert_vel_list):
    """
    Parameters
    ----------
    east_vel: float
        velocity of eastward movement of GPS station, calculated using the
        fit_all_gps_velocities function
    north_vel: float
        velocity of northward movement of GPS station, calculated using the
        fit_all_gps_velocities function
    up_vel: float
        velocity of upward movement of GPS station, calculated using the
        fit_all_gps_velocities function
    ----------
    Function plots the velocities of the given sites on map, using arrows
    for the east and north velocites and dots for the upwards velocities.
    """
    E = gps_df[east_vel_list]
    N = gps_df[north_vel_list]
    U = gps_df[vert_vel_list]

    norm = np.sqrt(E**2 + N**2)
    E_normalized = E / norm
    N_normalized = N / norm
    
    plt.figure(figsize=(10, 10))
    plt.quiver(gps_df['Longitude'], gps_df['Latitude'], E_normalized, N_normalized, scale=5, scale_units='xy', angles='xy', color='b', label='E and N velocities')
    
    plt.scatter(gps_df['Longitude'], gps_df['Latitude'], c=U, cmap='viridis', s=100, label='U Velocities')
    
    plt.xlim([gps_df['Longitude'].min() - 0.2, gps_df['Longitude'].max() + 0.2])
    plt.ylim([gps_df['Latitude'].min() - 0.2, gps_df['Latitude'].max() + 0.2])
    
    plt.title('East, North, and Upwards Velocities of GPS Stations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend()
    plt.colorbar(label='Up Velocities')
    plt.show()