import pandas as pd
import numpy as np
import inform_utils as inform
import glob
import xarray as xr
import datetime
from scipy.spatial import cKDTree
from datetime import time

def assign_flight_type(df):
    """
    Assigns flight type ('level' or 'profile') to each row of the input DataFrame based on stable altitude blocks 
    and gaps between these blocks. The function uses rolling standard deviation of altitude to identify level legs
    and combines consecutive blocks of stable altitude with a specified time gap threshold. Additionally, it labels 
    flight segments as "level" for level legs and "profile" for the aircraft vertical profile.

    Parameters:
    -----------
    df : pandas.DataFrame
        The input DataFrame with at least the following columns:
        - 'Time' (timestamp)
        - 'GGALT' (altitude in meters)

    Returns:
    --------
    pandas.DataFrame
        The input DataFrame with a new column 'flight_type', where each row is assigned a flight type:
        - 'level' for stable altitude periods
        - 'profile' for gaps between stable altitude blocks

    Example:
    --------
    df = pd.read_csv('flight_data.csv')  # Assuming the CSV contains relevant columns
    df_with_flight_types = assign_flight_type(df)
    """

    #-----------------------------------------
    #----- Find profiles and level legs ------
    #-----------------------------------------
    
    # Define a time gap threshold to combine blocks (e.g., 120 seconds)
    time_gap_threshold = pd.Timedelta(seconds=120)
    
    # Compute rolling standard deviation of altitude to smooth noise
    df['rolling_std'] = df['GGALT'].rolling(window=10, center=True).std()
    
    # Identify where altitude remains stable within the threshold
    df['stable'] = df['rolling_std'] < 3  # You can adjust the threshold (meters)
    
    # Assign unique block IDs when stability changes
    df['block_id'] = (df['stable'] != df['stable'].shift()).cumsum()
    
    # Group by block_id and filter for long-duration stable blocks
    block_info = df[df['stable']].groupby('block_id').agg(
        start_time=('Time', 'first'),
        end_time=('Time', 'last'),
        lower_bound=('GGALT', 'min'),  # Minimum altitude (lower bound)
        upper_bound=('GGALT', 'max'),  # Maximum altitude (upper bound)
        duration=('Time', lambda x: x.max() - x.min())
    )
    
    # Filter out short-duration blocks
    valid_blocks = block_info[block_info['duration'] > pd.Timedelta(seconds=150)] ## EDIT?
    
    # Sort the blocks by start time
    valid_blocks = valid_blocks.sort_values(by='start_time')
    
    # Define a time gap threshold to combine blocks (e.g., 120 seconds)
    time_gap_threshold = pd.Timedelta(seconds=120)
    
    # Combine consecutive blocks that are less than the threshold apart
    combined_blocks = []
    previous_block = valid_blocks.iloc[0]
    
    for idx, current_block in valid_blocks.iloc[1:].iterrows():
        # Check if the gap between the end time of the previous block and start time of the current block is below the threshold
        if current_block['start_time'] - previous_block['end_time'] <= time_gap_threshold:
            # Extend the previous block's end time to the current block's end time
            previous_block['end_time'] = current_block['end_time']
        else:
            # If the gap is too large, append the previous block and update to the current block
            combined_blocks.append(previous_block)
            previous_block = current_block
    
    # Add the last block after the loop
    combined_blocks.append(previous_block)
    
    # Convert combined blocks back to DataFrame
    combined_blocks_df = pd.DataFrame(combined_blocks)
    
    # --- Identify and Label "Profiles" between "Level" (Stable) sections ---
    
    # Create a new column 'flight_type' to categorize the blocks as "level" or "profile"
    combined_blocks_df['flight_type'] = 'level'  # By default, label as 'level'
    
    # Now identify the gaps between "level" blocks and label as "profile"
    profile_blocks = []
    for i in range(len(combined_blocks_df) - 1):
        end_time_current = combined_blocks_df.iloc[i]['end_time']
        start_time_next = combined_blocks_df.iloc[i + 1]['start_time']
        
        # If there's a gap between two 'level' blocks, label the gap as 'profile'
        if start_time_next - end_time_current > time_gap_threshold:
            # Assign 'profile' to the gap between two level blocks and calculate duration
            profile_duration = start_time_next - end_time_current  # Duration of the profile block
            
            profile_blocks.append({
                'start_time': end_time_current,
                'end_time': start_time_next,
                'flight_type': 'profile',
                'duration': profile_duration
            })
    
    # Convert 'profile_blocks' to DataFrame
    profile_blocks_df = pd.DataFrame(profile_blocks)
    
    # Append profile blocks to the original combined blocks DataFrame
    combined_blocks_with_profiles = pd.concat([combined_blocks_df, profile_blocks_df], ignore_index=True)
    
    # Sort again by time
    combined_blocks_with_profiles = combined_blocks_with_profiles.sort_values(by='start_time')
    
    # Check for "Profile" after the Last Level Block
    last_end_time = combined_blocks_with_profiles.iloc[-1]['end_time']
    last_time_in_data = df['Time'].max()
    
    if last_time_in_data - last_end_time > time_gap_threshold:
        # If the gap is greater than the threshold, consider it a "profile" block
        profile_block = pd.DataFrame([{
            'start_time': last_end_time,
            'end_time': last_time_in_data,
            'flight_type': 'profile',
        }])
    
        # Concatenate the new profile block to the existing DataFrame
        combined_blocks_with_profiles = pd.concat([combined_blocks_with_profiles, profile_block], ignore_index=True)
    
    # Check for "Profile" before the First Level Block, used for takeoff/landing
    first_start_time = combined_blocks_with_profiles.iloc[0]['start_time']
    first_time_in_data = df['Time'].min()
    
    if first_start_time - first_time_in_data > time_gap_threshold:
        profile_block_before_first = pd.DataFrame([{
            'start_time': first_time_in_data,
            'end_time': first_start_time,
            'flight_type': 'profile',
        }])
    
        combined_blocks_with_profiles = pd.concat([profile_block_before_first, combined_blocks_with_profiles], ignore_index=True)
    
    # List of columns to remove
    columns_to_remove = ['rolling_std','stable','block_id']
    # Drop the specified columns from df2
    df = df.drop(columns=columns_to_remove)
    
    # Add new column "flight_type" as either "level" or "profile"
    for _, row in combined_blocks_with_profiles.iterrows():
        flight_type = row['flight_type']
        # Find rows in df2 where the time is between start_time and end_time
        mask = (df['Time'] >= row['start_time']) & (df['Time'] <= row['end_time'])
        df.loc[mask, 'flight_type'] = flight_type
    # Assign the flight_type to the first few rows that fall before the first start_time in df1
    df.loc[df['Time'] < first_start_time, 'flight_type'] = df.iloc[0]['flight_type']

    #------------------------------
    #----- Find cloud layers ------
    #------------------------------
    # Ensure 'Time' is in datetime format
    df = df.copy()  # Avoid modifying original DataFrame
    df['Time'] = pd.to_datetime(df['Time'])
    
    # Find best match for column names dynamically
    plwc_col = next((col for col in df.columns if 'PLWCD' in col), None)
    concd_col = next((col for col in df.columns if 'CONCD' in col), None)

    # Add check if there are any cloudy periods
    if not plwc_col or not concd_col:
        print("Required columns not found. Skipping cloud detection.")
        final_cloud_blocks = pd.DataFrame(columns=['start_time', 'end_time', 'lower_bound', 'upper_bound', 'duration', 'Location'])
        df['cloud_status'] = 'Out-of-cloud'
        df['Location'] = 'Free'
    else:
        df['blocked'] = (df[plwc_col] > 0.001) & (df[concd_col] > 10)
        if not df['blocked'].any():
            print("No valid cloud blocks found. Skipping cloud layer logic.")
            final_cloud_blocks = pd.DataFrame(columns=['start_time', 'end_time', 'lower_bound', 'upper_bound', 'duration', 'Location'])
            df['cloud_status'] = 'Out-of-cloud'
            df['Location'] = 'Free'
        else:
            df['block_id'] = (df['blocked'] != df['blocked'].shift()).cumsum()
            block_info = df[df['blocked']].groupby('block_id').agg(
                start_time=('Time', 'first'),
                end_time=('Time', 'last'),
                lower_bound=('GGALT', 'min'),
                upper_bound=('GGALT', 'max'),
            )

        
            # Calculate duration directly by subtracting start_time from end_time
            block_info['duration'] = block_info['end_time'] - block_info['start_time']
            
            # Filter out short-duration blocks
            min_vertical = 30  # Adjust as needed (100 meters in your case)
            valid_blocks = block_info[(block_info['upper_bound'] - block_info['lower_bound']) > min_vertical].reset_index(drop=True)
            
            # Define the altitude difference and time gap thresholds
            altitude_gap_threshold = 200  # Increased altitude gap threshold
            # time_gap_threshold = pd.Timedelta(minutes=20)  # Time gap threshold for merging
            
            # Sort the valid blocks by their start time to process them in sequence
            valid_blocks = valid_blocks.sort_values(by='lower_bound')
            
            # Initialize a list to store combined blocks
            combined_blocks = []
            previous_block = valid_blocks.iloc[0].to_dict()
            
            # Iterate through the blocks and merge those that are within the thresholds
            for idx, current_block in valid_blocks.iloc[1:].iterrows():
                # Calculate the altitude gap between the current block's lower bound and the previous block's upper bound
                altitude_gap = abs(current_block['lower_bound'] - previous_block['upper_bound'])
                
                # Calculate the time gap between the current block's start time and the previous block's end time
                time_gap = current_block['start_time'] - previous_block['end_time']
                # Check if the altitude gap is within the threshold or if the time gap is within the allowed range for smaller altitudes
                if altitude_gap <= altitude_gap_threshold :
                    # If both criteria are met, merge the blocks
                    previous_block['end_time'] = max(previous_block['end_time'], current_block['end_time'])  # Get the latest end time
                    previous_block['start_time'] = min(previous_block['start_time'], current_block['start_time'])  # Get the earliest start time
                    previous_block['upper_bound'] = max(previous_block['upper_bound'], current_block['upper_bound'])  # Update upper bound
                    previous_block['lower_bound'] = min(previous_block['lower_bound'], current_block['lower_bound'])  # Update lower bound
                    
                    # Recalculate the duration for the merged block
                    previous_block['duration'] = previous_block['end_time'] - previous_block['start_time']
                else:
                    # If the blocks are far apart, save the previous block and move to the next one
                    combined_blocks.append(previous_block)
                    previous_block = current_block.to_dict()
            
            # Add the last block after the loop
            combined_blocks.append(previous_block)
            
            # Convert the merged blocks back into a DataFrame
            combined_blocks_df = pd.DataFrame(combined_blocks)
            
            # Second check for merging adjacent blocks in combined_blocks_df
            final_combined_blocks = []
            previous_block = combined_blocks_df.iloc[0].to_dict()
            
            # Apply additional check for merging based on both time and altitude gap
            for idx, current_block in combined_blocks_df.iloc[1:].iterrows():
                # Calculate the altitude gap and time gap
                altitude_gap = abs(current_block['lower_bound'] - previous_block['upper_bound'])
                time_gap = current_block['start_time'] - previous_block['end_time']
                
                # Check for overlap in the altitude ranges
                overlap_check = (current_block['lower_bound'] >= previous_block['lower_bound']) and (current_block['lower_bound'] <= previous_block['upper_bound'])
            
                # Check if both the altitude gap, time gap, or overlap condition is met
                if altitude_gap <= altitude_gap_threshold or overlap_check:
                    # Merge the blocks
                    previous_block['end_time'] = max(previous_block['end_time'], current_block['end_time'])
                    previous_block['start_time'] = min(previous_block['start_time'], current_block['start_time'])
                    previous_block['upper_bound'] = max(previous_block['upper_bound'], current_block['upper_bound'])
                    previous_block['lower_bound'] = min(previous_block['lower_bound'], current_block['lower_bound'])
                    
                    # Recalculate the duration for the merged block
                    previous_block['duration'] = previous_block['end_time'] - previous_block['start_time']
                else:
                    # Save the previous block and move to the next one
                    final_combined_blocks.append(previous_block)
                    previous_block = current_block.to_dict()
            
            # Add the last block after the loop
            final_combined_blocks.append(previous_block)
            
            # Convert the final combined blocks back into a DataFrame
            final_cloud_blocks = pd.DataFrame(final_combined_blocks)

            # Add 'cloud_status' based on whether altitude and time fall within any blocked region (in the cloud or out of cloud)
            df['cloud_status'] = 'Out-of-cloud'  # Default label
            # Loop through each block and label altitudes as "In-cloud" if they fall within the block's range
            for _, block in final_cloud_blocks.iterrows():
                # Create a mask that checks both altitude and time conditions
                mask = (
                    (df['GGALT'] >= block['lower_bound']) & (df['GGALT'] <= block['upper_bound']) &
                    (df['Time'] >= block['start_time']) & (df['Time'] <= block['end_time'])
                )
                
                # Apply the 'In-cloud' label where the mask is True
                df.loc[mask, 'cloud_status'] = 'In-cloud'
            
            # List of columns to remove
            columns_to_remove = ['blocked','block_id']
            # Drop the specified columns from df2
            df = df.drop(columns=columns_to_remove)
        
            df['Location'] = 'Free'
            
            # Find the minimum in-cloud altitude
            min_ic_alt = np.min(final_cloud_blocks['lower_bound'])-5
            mask = df.GGALT < min_ic_alt
            # Define 
            df.loc[mask, 'Location'] = 'BL'
        
            # Update the Location column based on the GGALT and cloud status
            df.loc[df['GGALT'] < min_ic_alt, 'Location'] = 'BL'
        
            # --- Add Location to final_cloud_blocks DataFrame ---
            # Add 'Location' based on the minimum in-cloud altitude
            final_cloud_blocks['Location'] = final_cloud_blocks['lower_bound'].apply(
                lambda x: 'BL' if x < min_ic_alt else 'Free'
            )
                # Add 'Location' based on the minimum in-cloud altitude
            combined_blocks_with_profiles['Location'] = combined_blocks_with_profiles['lower_bound'].apply(
                lambda x: 'BL' if x < min_ic_alt else 'Free'
            )

    # Sort the dataframe by Time for continuous time grouping
    df = df.sort_values(by='Time')
    # Remove rows where 'flight_type' is NaN
    df = df.dropna(subset=['flight_type'])
    # Create a new column 'block_id' to group continuous time periods based on flight_type, cloud_status, and Location
    df['block_id'] = (df['flight_type'] != df['flight_type'].shift()) | \
                      (df['cloud_status'] != df['cloud_status'].shift()) | \
                      (df['Location'] != df['Location'].shift())
    df['block_id'] = df['block_id'].cumsum()

    Final_ds = {'DataFrame': df,
                'flight_blocks': combined_blocks_with_profiles,
                'Cloud_blocks': final_cloud_blocks
               }
    
    return Final_ds

def block_flight(df):
    """
    Segments a flight dataset into different flight block categories based on cloud status, location, and flight type.

    Parameters:
    -----------
    df : pandas.DataFrame
        A DataFrame containing flight data with at least the following columns:
        - 'block_id' (int): Identifies different flight segments.
        - 'Location' (str): Can be 'BL' (Boundary Layer) or 'Free' airspace.
        - 'flight_type' (str): Can be 'level' or 'profile'.
        - 'cloud_status' (str): Either 'In-cloud' or 'Out-of-cloud'.
        - 'GGALT' (float): Altitude dbata, used for filtering profile segments.
        - 'Time' (datetime): Used to filter level flight segments.

    Returns:
    --------
    Flight_blocks : dict
        A dictionary containing categorized flight data:
        - 'Level BL': List of DataFrames for level flight in the boundary layer.
        - 'In-Cloud Profiles': List of DataFrames for in-cloud profile flights with altitude variation > 30m.
        - 'In-Cloud Level FT': List of DataFrames for level flights in free airspace within clouds.
        - 'Out-of-cloud Level FT': List of DataFrames for level flights in free airspace, lasting at least 3 minutes.

    Notes:
    ------
    - The function removes the first and last 'Level BL' periods to exclude takeoff/landing effects.
    - Only level flights lasting more than 180 seconds are included in 'Out-of-cloud Level FT'.
    - Profile flights are only included if their altitude change is greater than 30 meters.
    """
    # Find level BL periods
    out_of_cloud_bl = df[(df['Location'] == 'BL') & (df['flight_type'] == 'level')]
    bl_ids = sorted(out_of_cloud_bl['block_id'].unique())[1:-1] if len(out_of_cloud_bl['block_id'].unique()) > 2 else []
    bl_blocks_ds = [df[df['block_id'] == i] for i in bl_ids]
    
    # Find In-Cloud profile periods
    in_cloud_prof = df[(df['cloud_status'] == 'In-cloud') & (df['flight_type'] == 'profile')]
    ic_prof_ids = sorted(in_cloud_prof['block_id'].unique())
    ic_pro_blocks_ds = [df[df['block_id'] == i] for i in ic_prof_ids if df[df['block_id'] == i]['GGALT'].max() - df[df['block_id'] == i]['GGALT'].min() > 30]
    
    # Find level FT periods out-of-cloud
    level_ft = df[(df['cloud_status'] == 'Out-of-cloud') & (df['flight_type'] == 'level') & (df['Location'] == 'Free')]
    out_of_cloud_ft_ids = sorted(level_ft['block_id'].unique())
    level_ft_out_blocks_ds = [df[df['block_id'] == i] for i in out_of_cloud_ft_ids if df[df['block_id'] == i]['Time'].iloc[-1] - df[df['block_id'] == i]['Time'].iloc[0] > pd.Timedelta(seconds=180)]

    # Find level FT periods in-cloud
    level_ft_ic = df[(df['cloud_status'] == 'In-cloud') & (df['flight_type'] == 'level') & (df['Location'] == 'Free')]
    in_cloud_ft_ids = sorted(level_ft_ic['block_id'].unique())
    level_ft_ic_blocks_ds = [df[df['block_id'] == i] for i in in_cloud_ft_ids]
    
    # Save blocks of flight as dictionary for output
    Flight_blocks = {
        'Level BL': bl_blocks_ds,
        'In-Cloud Profiles': ic_pro_blocks_ds,
        'In-Cloud Level FT': level_ft_ic_blocks_ds,
        'Out-of-cloud Level FT': level_ft_out_blocks_ds
    }

    return Flight_blocks

def assign_cloud_type_HCR(flight_blocks, dir, idx: int = 0):
    """
    Assigns cloud echo type classifications from HCR (HIAPER-Cloud Radar) data 
    to flight data blocks within the global Flight_blocks variable.

    Parameters:
    -----------
    dir : str
        Base directory path where the RF (Research Flight) subfolders are located.
    idx : int, optional
        Index of the flight number (used to construct the folder name as 'RF{idx}'), 
        by default 0.

    Returns:
    --------
    dict
        Updated Flight_blocks dictionary with an added 'Echo_Type' column in each block, 
        indicating the radar-derived cloud classification at each time step.

    Notes:
    ------
    - Requires global Flight_blocks to be defined externally.
    - Each time in the flight data is matched with HCR timestamps to assign echo types.
    - Echo type values are pulled from the 'HCR_ECHO_TYPE_1D' variable in netCDF files.
    """

    dir_fold = dir + f"RF{idx+1:02d}" + '/'
    flight_paths = inform.find_flight_fnames(dir_fold)

    hcr_time = []
    echo_type_1D = []
    
    for file in flight_paths:
        nc = inform.open_nc(file)
        hcr_time.extend(np.array(nc.time))
        echo_type_1D.append(np.array(nc.HCR_ECHO_TYPE_1D))
    
    echo_type_1D = np.concatenate(echo_type_1D)
    
    for val in flight_blocks:
        block_type = flight_blocks[val]
        for i in range(len(block_type)):
            # block = block_type[i]
            block = block_type[i].copy()  # Make a copy to avoid SettingWithCopyWarning
            # Extract start and end time from the block
            start_time = block['Time'].iloc[0]
            end_time = block['Time'].iloc[-1]
            
            # Convert start_time and end_time to the same format as hcr_time if necessary
            # Assuming hcr_time is a list of datetime objects, convert if needed
            if isinstance(start_time, str):  # If start_time is in string format, convert it
                start_time = pd.to_datetime(start_time)
            if isinstance(end_time, str):  # If end_time is in string format, convert it
                end_time = pd.to_datetime(end_time)
    
            hcr_time_array = np.array(hcr_time)
            echo_column = np.full(len(block), np.nan)
    
            for j in range(len(block)):
                time_point = pd.to_datetime(block['Time'].iloc[j])
                match_indices = np.where(hcr_time_array == time_point)[0]
                if len(match_indices) > 0:
                    echo_column[j] = echo_type_1D[match_indices[0]]
    
            block.loc[:, 'Echo_Type'] = echo_column  # <- Use loc for safe assignment
            block_type[i] = block
    
        flight_blocks[val] = block_type
        
    return flight_blocks


# High-Level function
def VAP_process_flight_data(df,i,dir):
    """
    High-Level Function for Processing Flight Data in Value Added Products.

    This function serves as the main entry point for processing flight data. It first calls 
    `assign_flight_type` to assign flight types (e.g., 'level' or 'profile') to different segments of the flight 
    based on altitude stability and time gaps. After flight types are assigned, it proceeds to categorize the data 
    into different flight blocks (e.g., level flight in boundary layer, in-cloud profile flight, etc.) by calling 
    the `block_flight` function.

    Parameters:
    -----------
    df : pandas.DataFrame
        A DataFrame containing flight data with at least the following columns:
        - 'Time' (datetime): Time of each flight record.
        - 'GGALT' (float): Altitude of the aircraft.
        - 'PLWCD_' (float): Cloud Droplet Probe LWC.
        - 'CONCD_' (float): Cloud Droplet Probe Number Concentration.

    Returns:
    --------
    dict
        A dictionary containing:
        - 'DataFrame': A modified DataFrame with assigned flight types, cloud status, and location.
        - 'flight_blocks': A dictionary of flight blocks categorized by flight type and cloud status.
        - 'cloud_blocks': A dataframe of flight blocks including blocks of aircraft data inside cloud layers.

    Notes:
    ------
    - The `assign_flight_type` function is responsible for determining whether the flight segments are 'level' or 'profile'.
    - The `block_flight` function segments the flight data based on the assigned flight types and cloud status into specific blocks (e.g., 'Level BL', 'In-Cloud Profiles', etc.).
    - The function ensures proper labeling of different flight segments for further analysis, including cloud status and location (e.g., boundary layer or free airspace).
    """
    # Function to assign flight type "Level" and "Profile" when in/out of cloud
    dict_flight_type = assign_flight_type(df)

    # Extract dataframe that has been modified from the assign_flight_type function
    df_mod = dict_flight_type['DataFrame']
    # Plot time series of aircraft defined flight blocks
    # plot_block_ts(dict_flight_type,i)

    # Run block flight function to return list of Dataframes of "blocked" flight data
    flight_blocks = block_flight(df_mod)
    # Function to assign cloud type from the HCR data
    # flight_block_comp = assign_cloud_type_HCR(flight_blocks,dir,i)
    
    # Plot time series of HCR defined cloud types  
    # plot_hcr_cloud_type(df_mod,flight_block_comp,i)
    return flight_blocks

def select_ERA5_4flight(df):
    # Define function to filter ERA5 files based on time
    def get_matching_files(pattern, start_dt, end_dt):
        file_list = glob.glob(pattern)
        selected = []
        for file in file_list:
            time_strs = file.split('.')[-2].split('_')
            file_start = datetime.datetime.strptime(time_strs[0], "%Y%m%d%H")
            file_end = datetime.datetime.strptime(time_strs[1], "%Y%m%d%H")
            if file_start <= end_dt and file_end >= start_dt:
                selected.append(file)
        return selected
        
    # Extract the times of the research flight
    month, year = df.Time[0].month, df.Time[0].year
    day_start,day_end = df.Time[0].day, df.Time.iloc[-1].day
    start_hour, end_hour = df.Time[0].hour, df.Time.iloc[-1].hour
    
    # Select the latitude/longitude box to reduce size of era5 data
    lat_max, lat_min = np.floor(df.GGLAT.min()), np.ceil(df.GGLAT.max())
    lon_min, lon_max = np.floor(df.GGLON.min()), np.ceil(df.GGLON.max())
    
    # Flight start and end times
    start_dt = datetime.datetime(year, month, day_start, start_hour) 
    end_dt = datetime.datetime(year, month, day_end, end_hour)+datetime.timedelta(hours=1)
    
    # Make the yearmonth string for file selection
    dir_date = f"{year}{month:02d}"
    
    # Load SST data
    filepath="/glade/campaign/collections/rda/data/ds633.0/e5.oper.an.sfc/"
    # # Construct the search pattern (SST)
    path = f"{filepath}{dir_date}/*_sstk.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_sst = xr.open_dataset(file[0])
    
    ds_sst = ds_sst.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    )
    # Load 2m tempeature
    path = f"{filepath}{dir_date}/*_2t.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_2mt = xr.open_dataset(file[0])# <- Should work now
    ds_2mt = ds_2mt.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    )
    
    # Load 10m wind speed (u and v components)
    path = f"{filepath}{dir_date}/*_10u.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_m10u = xr.open_dataset(file[0])# <- Should work now
    ds_m10u = ds_m10u.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    )
    path = f"{filepath}{dir_date}/*_10v.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_m10v = xr.open_dataset(file[0])# <- Should work now
    ds_m10v = ds_m10v.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    )
    
    ws = np.sqrt(ds_m10u.VAR_10U**2 + ds_m10v.VAR_10V**2)
    wind_dir = (270 - np.degrees(np.arctan2(ds_m10v.VAR_10V, ds_m10u.VAR_10U))) % 360
    
    # Load w data for all pressure levels
    filepath="/glade/campaign/collections/rda/data/ds633.0/e5.oper.an.pl/"
    # # Construct the search pattern (SST)
    path = f"{filepath}{dir_date}/*_w.*.nc"
    files = get_matching_files(path, start_dt, end_dt)
    ds_wpl = xr.open_mfdataset(files)# <- Should work now
    
    # Select w at 500 hPa
    w_500 = ds_wpl.W.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    level=500
    )
    w_800 = ds_wpl.W.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    level=800
    )
    
    # Load pressure level wind speed (u and v components)
    path = f"{filepath}{dir_date}/*_u.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_upl = xr.open_dataset(file[0])# <- Should work now
    ds_upl = ds_upl.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    level=800,
    )
    path = f"{filepath}{dir_date}/*_v.*.nc"
    file = get_matching_files(path, start_dt, end_dt)
    ds_vpl = xr.open_dataset(file[0])# <- Should work now
    ds_vpl = ds_vpl.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    level=800,
    )
    
    ws800 = np.sqrt(ds_upl.U**2 + ds_vpl.V**2)
    
    wind_shear = ws800-ws
    
    # Load upper temperature data with select pressure levels
    path = f"{filepath}{dir_date}/*_t.*.nc"
    files = get_matching_files(path, start_dt, end_dt)
    ds_tpl = xr.open_mfdataset(files)# <- Should work now
    ds_tpl = ds_tpl.sel(
    latitude=slice(lat_min, lat_max),  # Select latitudes within range
    longitude=slice(lon_min, lon_max),  # Select longitudes within range
    time=slice(start_dt, end_dt),
    )
    
    # Calculate M-value
    Rd = 287
    Cp = 1005     
    theta_sfc = ds_sst.SSTK*(1)**(Rd/Cp)
    theta_800 = ds_tpl.T.sel(level=800)*(1013.25/800)**(Rd/Cp)
    
    M = theta_sfc.T - theta_800.T
    M = M.transpose("time", "latitude", "longitude")
    
    dt = ds_2mt.VAR_2T - ds_sst.SSTK
    
    # Merge the dataset variables used later
    ds = {
    'deltaT': dt, 
    'M': M,
    'w_500': w_500,
    'w_800': w_800,
    'SST': ds_sst.SSTK,
    'WS': ws,
    'Wind_shear': wind_shear
     }

    return ds

def collocate_ERA5_dat(ds, blocks):
    # Create KDTree from ERA5 lat/lon grid
    M, w_500, w_800, sst, dt, ws, wsh = ds['M'], ds['w_500'], ds['w_800'], ds['SST'], ds['deltaT'], ds['WS'], ds['Wind_shear']
    lat_vals = w_500.latitude.values
    lon_vals = w_500.longitude.values
    lon_grid, lat_grid = np.meshgrid(lon_vals, lat_vals)
    points = np.column_stack((lat_grid.ravel(), lon_grid.ravel()))
    tree = cKDTree(points)
    
    era5_times = M.time.values.astype('datetime64[ns]')
    
    # "load" data to speed up code
    M_loaded = M.transpose("time", "latitude", "longitude").compute()
    w500_loaded = w_500.transpose("time", "latitude", "longitude").compute()
    w800_loaded = w_800.transpose("time", "latitude", "longitude").compute()    
    
    # # Iterate through blocks
    for val in blocks:
        block_type = blocks[val]
        
        for i in range(len(block_type)):
            block = block_type[i].copy()
            # Drop rows with NaN in lat/lon
            block = block.dropna(subset=['GGLAT', 'GGLON']).copy()
            # print(i)
            # Vectorized time and spatial nearest match
            flight_times = block['Time'].astype('datetime64[ns]').values
            flight_lats = block['GGLAT'].values
            flight_lons = block['GGLON'].values
            
            # Nearest ERA5 time
            time_indices = np.abs(era5_times[:, None] - flight_times).argmin(axis=0)
            nearest_times = era5_times[time_indices]
            
            # Nearest ERA5 spatial point via KDTree
            _, idxs = tree.query(np.column_stack((flight_lats, flight_lons)))
            lat_idxs, lon_idxs = np.unravel_index(idxs, lat_grid.shape)
            nearest_lats = lat_vals[lat_idxs]
            nearest_lons = lon_vals[lon_idxs]
            
            # Unique key set for reuse
            keys = list(zip(nearest_times, nearest_lats, nearest_lons))
            unique_keys = list(set(keys))
            
            # Lookups for SST values
            sst_lookup = {}
            
            for t, lat, lon in unique_keys:
                try:
                    # SST
                    sst_val = sst.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    sst_lookup[(t, lat, lon)] = sst_val
                except Exception:
                    sst_lookup[(t, lat, lon)] = np.nan
    
            # Assign back to DataFrame
            block['ERA5_SST'] = [sst_lookup.get(k, np.nan) for k in keys]
            
            # M lookup is just the precomputed M values
            M_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    m_val = M_loaded.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    M_lookup[(t, lat, lon)] = m_val
                except Exception:
                    M_lookup[(t, lat, lon)] = np.nan
            block['M'] = [M_lookup.get(k, np.nan) for k in keys]
            
            # w_500 lookup
            w500_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    w_val = w500_loaded.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    w500_lookup[(t, lat, lon)] = w_val
                except Exception:
                    w500_lookup[(t, lat, lon)] = np.nan
            block['w500'] = [w500_lookup.get(k, np.nan) for k in keys]# Update the block
            block_type[i] = block
            
            # w_800 lookup
            w800_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    w_val = w800_loaded.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    w800_lookup[(t, lat, lon)] = w_val
                except Exception:
                    w800_lookup[(t, lat, lon)] = np.nan
            block['w800'] = [w800_lookup.get(k, np.nan) for k in keys]# Update the block
            block_type[i] = block
            
            # delta_T lookup 
            dt_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    dt_val = dt.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    dt_lookup[(t, lat, lon)] = dt_val
                except Exception:
                    dt_lookup[(t, lat, lon)] = np.nan
            block['deltaT'] = [dt_lookup.get(k, np.nan) for k in keys]# Update the block
            block_type[i] = block
            
            # Wind_speed lookup 
            ws_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    ws_val = ws.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    ws_lookup[(t, lat, lon)] = ws_val
                except Exception:
                    ws_lookup[(t, lat, lon)] = np.nan
            block['Wind_sp'] = [ws_lookup.get(k, np.nan) for k in keys]# Update the block
            block_type[i] = block
    
            # Wind shear lookup 
            wsh_lookup = {}
            for t, lat, lon in unique_keys:
                try:
                    wsh_val = wsh.sel(time=t, latitude=lat, longitude=lon, method="nearest").values.item()
                    wsh_lookup[(t, lat, lon)] = wsh_val
                except Exception:
                    wsh_lookup[(t, lat, lon)] = np.nan
            block['Wind_shear'] = [wsh_lookup.get(k, np.nan) for k in keys]# Update the block
            block_type[i] = block
            
        blocks[val] = block_type
        
    return blocks

def cloud_regime(fblks):
    # Iterate through blocks
    for val in fblks:
        block_type = fblks[val]
        for i in range(len(block_type)):
            block = block_type[i].copy()
            block['cloud_regime'] = pd.Series('Undetermined', index=block.index, dtype='object')
            condition_cum = ((block['M'] > -7) & (block['Wind_shear'] < 6)) | ((block['M'] > -7) & (block['Wind_sp'] > 10))
            condition_strcu = ((block['M'] <= -10) & (block['Wind_sp'] < 10)) | ((block['M'] <= -10) | (block['Wind_shear'] > 6))
            # Assign values based on conditions
            block.loc[condition_cum, 'cloud_regime'] = 'Open-Cell Cu'
            block.loc[condition_strcu, 'cloud_regime'] = 'Stratiform'
    
            block_type[i] = block
    
        fblks[val] = block_type

    return fblks

def write_RF_nc(fblks_cr, rf):
    combined = []
    if isinstance(fblks_cr, dict):
        for label, df_list in fblks_cr.items():
            for i, df in enumerate(df_list):
                df = df.copy()
                df["flight"] = rf
                df["block_label"] = label
                df["block_index"] = i
                combined.append(df)

        df_all = pd.concat(combined, ignore_index=True)
        df_all = df_all.set_index(["block_label", "block_index", "Time"])
        ds = df_all.reset_index().to_xarray()

        name = f"{rf}.nc"
        ds.to_netcdf(name)
        print(f"Wrote {name}")

def plot_block_ts(dict,idx):

    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.dates as mdates
    import numpy as np
    import pandas as pd

    # Assuming the four DataFrames are already created
    # profile_in_cloud, level_in_cloud, level_out_cloud_bl, level_out_cloud_fr
    # Dict = assign_flight_type(df)

    df = dict['DataFrame']
    # print(df)
    blocks = dict['flight_blocks']
    incloud = dict['cloud_blocks']
    # Creating the four DataFrames based on flight_type, cloud status, and Location
    profile_in_cloud = df[(df['flight_type'] == 'profile') & (df['cloud_status'] == 'In-cloud')]
    level_in_cloud = df[(df['flight_type'] == 'level') & (df['cloud_status'] == 'In-cloud') & (df['Location'] != 'BL')]
    level_out_cloud_bl = df[(df['flight_type'] == 'level') & (df['cloud_status'] != 'In-cloud') & (df['Location'] == 'BL')]
    level_out_cloud_fr = df[(df['flight_type'] == 'level') & (df['cloud_status'] != 'In-cloud') & (df['Location'] == 'Free')]
    # Create figure and GridSpec layout
    fig = plt.figure(figsize=(14, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2.7, 1])  # First subplot is 3x the width of the second

    # First subplot (larger)
    ax1 = fig.add_subplot(gs[0])  # Assigning first subplot

    # Plot flight altitude for each DataFrame in different colors
    ax1.plot(df['Time'], df['GGALT'], color='k', linewidth=3)

    # Plot In-cloud, Level In-cloud, and other data
    ax1.scatter(profile_in_cloud['Time'], profile_in_cloud['GGALT'], color='red', label='Profile In-cloud', marker='s', s=1, zorder=2)
    ax1.scatter(level_in_cloud['Time'], level_in_cloud['GGALT'], color='blue', label='Level In-cloud', marker='s', s=1, zorder=2)
    ax1.scatter(level_out_cloud_bl['Time'], level_out_cloud_bl['GGALT'], color='green', label='Level Out-of-cloud (BL)', marker='s', s=1, zorder=2)
    ax1.scatter(level_out_cloud_fr['Time'], level_out_cloud_fr['GGALT'], color='purple', label='Level Out-of-cloud (Free)', marker='s', s=1, zorder=2)

    # Set x-axis limits
    start_limit = df['Time'].min()
    end_limit = df['Time'].max()
    ax1.set_xlim([start_limit, end_limit])

    # Format x-axis to show only hours, minutes, and seconds
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))  # Adjust format as needed
    fig.autofmt_xdate()

    # Shade blocks according to their type (level or profile)
    for _, row in blocks.iterrows():
        start_time, end_time, flight_type = row['start_time'], row['end_time'], row['flight_type']
        if flight_type == 'level':
            ax1.axvspan(start_time, end_time, color='blue', alpha=0.3, label="Level leg" if 'Level leg' not in ax1.get_legend_handles_labels()[1] else None)
        elif flight_type == 'profile':
            ax1.axvspan(start_time, end_time, color='goldenrod', alpha=0.5, label="Profiling" if 'Profiling' not in ax1.get_legend_handles_labels()[1] else None)

    # Labels and title
    ax1.set_xlabel('Time UTC (MM-dd HH:mm)')
    ax1.set_ylabel('Altitude (m)')
    ax1.set_title('Altitude Time Series separating into "Level legs" and "Profiles"')
    ax1.set_ylim(-200, np.max(df['GGALT'] + 600))
    ax1.legend(loc='upper right', ncol=6, markerscale=6,fontsize=8)
    ax1.grid(True)

    # Second subplot (smaller)
    ax2 = fig.add_subplot(gs[1])  # Assigning second subplot

    # Scatter plot for concentration and altitude
    ax2.scatter(df.CONCD_RWIO, df.GGALT, color='b', label='CDP', alpha=0.5, marker='^', s=4)

    # Log scale for x-axis
    ax2.set_xscale('log')
    ax2.set_xlabel('Conc (#/cm3)')
    ax2.set_ylabel('Altitude (meters)')
    ax2.grid(True)
    ax2.set_xlim(.01, 1000)

    # Add second x-axis on top
    ax2_top = ax2.twiny()
    ax2_top.plot(df.PLWCD_RWIO, df.GGALT, color='orange', alpha=.7, linestyle='--', label='CDP LWC')
    ax2_top.set_xlabel('g/m3')
    ax2_top.set_xscale('log')
    ax2_top.set_xlim(0.0001, 10)
    ax2.set_ylim(-200, np.max(df['GGALT'] + 600))

    # Shade blocked altitude regions in ax2
    for i, row in incloud.iterrows():
        ax2.fill_betweenx(
            y=[row['lower_bound'], row['upper_bound']],  # Altitude range for shading
            x1=0.01,  # Left bound (min x-value)
            x2=1000,  # Right bound (max x-value)
            color='red', alpha=0.3, label="Cloud layer" if 'Cloud layer' not in ax2.get_legend_handles_labels()[1] else None
        )

    # Merge legends from both axes
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_top.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')  # Merge legends from both axes

    # Reorder the legends if needed
    all_lines = lines + lines2
    all_labels = labels + labels2
    if len(all_labels) >= 3:
        new_order = [0, 2, 1]  # Modify based on the desired order
        all_lines = [all_lines[i] for i in new_order]
        all_labels = [all_labels[i] for i in new_order]

    # Apply reordered legend
    ax2.legend(all_lines, all_labels, loc='upper right', markerscale=3)

    # Adjust layout to prevent overlap
    plt.tight_layout()
    fig.subplots_adjust(wspace=0.12)  # Increase spacing between subplots

    # Save the figure
    rf_id = f"RF_{idx+1:02d}"
    filename = f"SOCRATES_Altitude_Flight_Cloud_type_25Hz_{rf_id}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')  # Save as PNG with high resolution

   
def plot_hcr_cloud_type(df,Flight_blocks,idx):
    
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.colors import ListedColormap, BoundaryNorm
    import matplotlib.dates as mdates
    
    # Initialize figure and gridspec for plotting
    fig = plt.figure(figsize=(14, 6))
    gs = fig.add_gridspec(2, 1, height_ratios=[10, 1])
    
    ax1 = fig.add_subplot(gs[0, 0])  # Main altitude plot
    ax2 = fig.add_subplot(gs[1, 0])  # Echo Type plot
    
    tick_values = [14, 16, 18, 25, 30, 32, 34, 36, 38]
    
    # Update to use the new colormap interface
    spectral_cmap = plt.colormaps['Set1']  # Access colormap directly
    tick_to_color = {tick: spectral_cmap(i / len(tick_values)) for i, tick in enumerate(tick_values)}  # Map each tick to a color
       
    # Plot flight altitude for each DataFrame in different colors
    ax1.plot(df['Time'], df['GGALT'], color='k', linewidth=3)
    
    start_limit = df['Time'].min()
    end_limit = df['Time'].max()
    ax1.set_xlim([start_limit, end_limit])
    
    for val in Flight_blocks:
        block_type = Flight_blocks[val]
        for i in range(len(block_type)):
            block = block_type[i]
            start_time = block['Time'].iloc[0]
            end_time = block['Time'].iloc[-1]
            mean_echo_type = np.nanmean(block['Echo_Type'])
        
            # Find the closest tick value and corresponding color
            closest_tick = tick_values[np.argmin(np.ceil(np.abs(np.array(tick_values) - mean_echo_type)))]
            color = tick_to_color[closest_tick]
        
            # Shade region on ax1
            ax1.axvspan(start_time, end_time, color=color, alpha=0.8)
    
            # Plot scatter on ax2
            ax2.scatter(
                block.Time,
                np.zeros(len(block.Time)),
                c=block.Echo_Type,
                cmap='Set1',
                marker='s',
                s=4,
                vmin=min(tick_values),
                vmax=max(tick_values)
            )
    
    # start_time = pd.to_datetime("2018-01-16 01:30:00")
    # end_time = pd.to_datetime("2018-01-16 03:00:00")
    # ax1.set_xlim(start_time, end_time)
    ax1.set_ylabel('Altitude (m)')
    # Clean up ax2 to make it look like a color strip
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_yticks([])
    ax2.set_xlabel('Time UTC (MM-dd HH:mm)')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    fig.autofmt_xdate()
    # Set x-axis limits
    
    ax2.set_xlim([start_limit, end_limit])
    
    # Define the tick values (bin labels)
    tick_values = [14, 16, 18, 25, 30, 32, 34, 36, 38]
    tick_labels = [
        "stratiform low",
        "stratiform mid",
        "stratiform high",
        "mixed",
        "convective",
        "conv. elevated",
        "conv. shallow",
        "conv. mid",
        "conv. deep"
    ]
    # We need to define edges for each bin; to get N blocks, we need N+1 boundaries
    bounds = list(range(len(tick_values) + 1))  # e.g., 0, 1, 2, ..., 9
    
    # Create a colormap with N colors
    colors = plt.cm.Set1(np.linspace(0, 1, len(tick_values)))
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N)
    
    # Add vertical colorbar on the right
    cbar = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        ax=[ax1, ax2],
        orientation='vertical',
        ticks=np.arange(len(tick_values)) + 0.5,  # Tick in the center of each block
        pad=0.012
    )
    # Set category labels instead of numbers
    cbar.ax.set_yticklabels(tick_labels)
    # Set colorbar labels and title
    cbar.ax.set_yticklabels(tick_labels)
    cbar.set_label("HCR Echo Type")
    # Turn ticks inside for all three axes
    for ax in [ax1, ax2]:
        ax.tick_params(direction='in', which='both', top=True, right=True)
    # # Show the plot
    # plt.show()

    # Save the figure
    rf_id = f"RF_{idx+1:02d}"
    filename = f"SOCRATES_Altitude_Flight_HCR_Cloud_Echo_{rf_id}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')  # Save as PNG with high resolution






