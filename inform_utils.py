import netCDF4
import pathlib as path
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from fnmatch import fnmatch
from typing import Iterable
import xarray as xr

def find_flight_fnames(dir_path: str) -> list[str]:
    """
    find_flight_fnames just searches a directory for all *.nc files and returns a list of them.

    :param dir_path: a path to the directory containing flight netcdf files

    :return: Returns a list of flight netcdf files.
    """
    flight_paths=[]
    flight_fnames = sorted([fname for fname in os.listdir(dir_path) if fnmatch(fname, "*.nc")])
    for i in range(len(flight_fnames)):
        flight_paths.append(dir_path + '/' + flight_fnames[i])
    
    return flight_paths

def find_nc_fnames(dir_path: str) -> list[str]:
    """
    find_flight_fnames just searches a directory for all *.nc files and returns a list of them.
    
    :param dir_path: a path to the directory containing flight netcdf files
    
    :return: Returns a list of flight netcdf files.
    """
    nc_paths=[]
    nc_fnames = sorted([fname for fname in os.listdir(dir_path) if fnmatch(fname, "*.nc")])
    for i in range(len(nc_fnames)):
        nc_paths.append(dir_path + '/' + nc_fnames[i])
        
        nudg_path = [file for file in nc_paths if ".hs." in file]
        free_path = [file for file in nc_paths if ".h0." in file]
        # save dictionary with the paths for 
        paths = {'Free': free_path,'Nudg': nudg_path}
        
    return paths

def open_nc(flight_paths: str) -> netCDF4._netCDF4.Dataset:
    """
    open_flight_nc simply checks to see if the file at the provided path string exists and opens it.

    :param file_path: A path string to a flight data file, e.g. "./test/test_flight.nc"

    :return: Returns xr.open_dataset object.
    """
    fp_path = path.Path(flight_paths)
    if not fp_path.is_file():
        raise FileNotFoundError('testing excptions')

    return xr.open_dataset(flight_paths)

def read_flight_nc_1hz(nc: xr.open_dataset, read_vars) -> pd.DataFrame:
    """
    read_flight_nc reads a set of variables into memory.

    NOTE: a low-rate, 1 Hz, flight data file is assumed

    :param nc: netCDF4._netCDF4.Dataset object opened by open_flight_nc.
    :param read_vars: An list of strings of variable names to be read into memory.

    :return: Returns a pandas data frame.
    """
    long_names = [nc[var].long_name if 'long_name' in nc[var].attrs else None for var in read_vars]
    data = [] # an empty list to accumulate Dataframes of each variable to be read in
    for var in read_vars:
        try:
            if var == "Time":
                # df = xr.open_dataset(nc)
                time = np.array(nc.Time)
                data.append(pd.DataFrame({var: time}))
                # dt_list = sfm_to_datetime(time, tunits)
                # data.append(pd.DataFrame({'datetime': time}))
            else:
                output = nc[var][:]
                data.append(pd.DataFrame({var: output}))
        except Exception as e:
            print(f"Issue reading {var}: {e}")
            pass
    
    dataframe = pd.concat(data, axis=1, ignore_index=False)
    dataframe.attrs['long_names'] = long_names
    # concatenate the list of dataframes into a single dataframe and return it
    return dataframe

def read_flight_nc_25hz(nc: xr.open_dataset, read_vars) -> pd.DataFrame:
    """
    read_flight_nc reads a set of variables into memory.
    
    NOTE: a high-rate, usually 25 Hz, flight data file is assumed.
    
    :param nc: netCDF4._netCDF4.Dataset object opened by open_flight_nc.
    :param read_vars: An optional list of strings of variable names to be read into memory. A default
                      list, vars_to_read, is specified above. Passing in a similar list will read in those variables
                      instead.
    
    :return: Returns a pandas data frame.
    """
    data = []
    sub_seconds = np.arange(0, 25, 1)/25.
    hz = 25
    for var in read_vars:
        try:
            if var == "Time":
                time = nc[var].values  # Get NumPy array from Xarray
                # Convert sub_seconds into timedelta in nanoseconds
                sub_seconds_ns = (sub_seconds * 1e9).astype('timedelta64[ns]')
                # Expand time into 2D, add sub-second offsets
                time_25hz = time[:, None] + sub_seconds_ns
                output = time_25hz.ravel()  # Flatten to 1D
                data.append(pd.DataFrame({var: output}))
            else:
                ndims = len(np.shape(nc[var][:]))
                if ndims == 2:
                    # 2-D, 25 Hz variables can just be raveled into 1-D time series
                    output = np.ravel(nc[var].values)
                    data.append(pd.DataFrame({var: output}))
                elif ndims == 1:
                    values = nc[var].values  # Extract as NumPy array
                    if values.shape[0] != len(time):  # Interpolation case (e.g., GGALT-style)
                        print(f"Skipping {var} due to shape mismatch: {values.shape[0]} != {len(time)}")
                        continue
                    # Interpolate to 25 Hz (fudged interpolation)
                    output_2d = np.full((len(values), hz), np.nan)
                    for i in range(len(values) - 1):
                        output_2d[i, :] = values[i] + sub_seconds * (values[i+1] - values[i])
                    output = output_2d[:-1].ravel()  # remove the last NaN row
                    data.append(pd.DataFrame({var: output}))
        except Exception as e:
            print(f"Issue reading {var}: {e}")
            pass
    # concatenate the list of dataframes into a single dataframe and return it
    dataframe = pd.concat(data, axis=1, ignore_index=False)
    return dataframe

def read_flight_nc(nc: xr.open_dataset, vars2read: list[str]) -> pd.DataFrame:
    """
    read_flight_nc simply figures out if the flight netcdf object is 1 hz or 25 hz and calls the appropriate reader.

    :param nc: A netcdf object for a flight netcdf file.
    :param read_vars: A list of variable names to be read in the netcdf object. Optional. Default is "vars_to_read" specified
                      above.

    :return: Returns Pandas DataFrame
    """
    dim_names = list(nc.dims)
    if 'sps25' in dim_names:
        df = read_flight_nc_25hz(nc, vars2read)
    else:
        df = read_flight_nc_1hz(nc, vars2read)
    return df

# Function to read in all the relevant variables from the NSF aircraft datasets
def read_vars(nc):

    var_list = nc.data_vars
    time = 'Time'
    # Spatial variables
    lat, lon, alt = 'GGLAT', 'GGLON', 'GGALT'
    
    # state variables
    temp = 'ATX'
    dwpt = 'DPXC'
    u = 'UIC' if 'UIC' in var_list else 'UIX'
    v = 'VIC' if 'VIC' in var_list else 'VIX'
    w = 'WIC' if 'WIC' in var_list else 'WIX'
    p = 'PSXC'
    ew = 'EWX'
    rh = 'RHUM'
    vars_to_read = [time, lat, lon, alt, temp, dwpt, u,  w, p, ew, rh]
    # Thermodynamic data
    if any('THETA' in var for var in var_list): 
        theta_vars = [var for var in var_list if 'THETA' in var and ('_GP' not in var)]
        vars_to_read.extend(theta_vars)
    # Cloud microphysical
    if any('CONC' in var for var in var_list): # cloud concentrations
        conc_vars = [var for var in var_list if 'CONC' in var and 'D' in var and ('R_' not in var and 'CN' not in var and \
                    'CV' not in var and '0_' not in var and 'UD' not in var)]
        # print(conc_vars)
        vars_to_read.extend(conc_vars)
    if any('PLW' in var for var in var_list): # Liquid/Ice water contents
        # v = [var for var in var_list if '2' not in var]
        wc_vars = [var for var in var_list if 'PLW' in var and ('2V' not in var)]
        vars_to_read.extend(wc_vars)
    # Aerosol data
    if any('UHSAS' in var for var in var_list) or any('CONCN' in var for var in var_list):
        aer_var = [var for var in var_list if ('UHSAS' in var or 'CONCU' in var or 'CONCN' in var) and ('AU' not in var and 'UD'  not in var and 'CUH' not in var and 'CFDC' not in var)]
        # uhsas_cells = var_list['CUHSAS_LWII'].CellSizes
        vars_to_read.extend(aer_var)
    # print("Loaded variables:")
    # print(vars_to_read)
    return vars_to_read

def read_sizedist_vars(nc):
    # Ensure we’re iterating over plain strings (variable names)
    names = list(nc.data_vars.keys())

    out = []
        # Include Time if present (coord or data var)
    if 'Time' in nc:
        out.append('Time')
        
    def add_prefix(prefix, exclude_substr=None):
        for n in names:
            if n.startswith(prefix) and (exclude_substr is None or exclude_substr not in n):
                out.append(n)

    # Cloud probe size distributions
    add_prefix('CCDP')
    add_prefix('C2DCA')
    add_prefix('C2DSA')          # <-- startswith enforces "at the start"

    # Aerosol size distributions
    add_prefix('CUHSAS', exclude_substr='CVI')   # exclude any CUHSAS* containing CVI
    add_prefix('CS200') # PCASP

    # Deduplicate while preserving original order
    out = list(dict.fromkeys(out))
    
    return out

def _prep_probe(nc, varname):
    da = nc[varname]
    # collapse any sps* to 1 Hz
    sps_dims = [d for d in da.dims if d.lower().startswith('sps')]
    if sps_dims:
        da = da.mean(dim=sps_dims, keep_attrs=True)
    # find bin dim and order (Time, Bin)
    bin_dim = next(d for d in da.dims if d.lower().startswith(('vector','bin','cell')))
    time_name = 'Time' if 'Time' in da.dims else 'time'
    da = da.transpose(time_name, bin_dim)

    # restrict to used bins
    first_bin = int(da.attrs.get('FirstBin', 0))
    last_bin  = int(da.attrs.get('LastBin', da.sizes[bin_dim]-1))
    da = da.isel({bin_dim: slice(first_bin, last_bin+1)})
    nbins = da.sizes[bin_dim]

    # upper edges for used bins
    cells_all = np.asarray(da.attrs.get('CellSizes', []), dtype=float)
    if cells_all.size == 0:
        raise ValueError(f"{varname} missing CellSizes attr")
    cells_used = cells_all[first_bin:last_bin+1]  # length == nbins

    return da, bin_dim, time_name, cells_used, nbins

def _sum_range_by_upper_edge(da, bin_dim, cells_used, lower_um=None, upper_um=None):
    """Sum across bins chosen by upper-edge thresholds."""
    nbins = da.sizes[bin_dim]

    if lower_um is None and upper_um is None:
        raise ValueError("Provide at least lower_um or upper_um")

    # choose start
    if lower_um is None:
        i0 = 0
    else:
        i0 = int(np.searchsorted(cells_used, lower_um, side='left'))

    # choose end (inclusive)
    if upper_um is None:
        i1 = nbins - 1
    else:
        i1 = int(np.searchsorted(cells_used, upper_um, side='right')) - 1

    i0 = np.clip(i0, 0, nbins - 1)
    i1 = np.clip(i1, 0, nbins - 1)

    if i1 < i0:
        # empty selection → NaNs (shape preserves time axis)
        return da.isel({bin_dim: slice(0, 0)}).sum(dim=bin_dim) * np.nan

    return da.isel({bin_dim: slice(i0, i1 + 1)}).sum(dim=bin_dim, skipna=True)

def calc_concs_from_sd(sizedist_vars, nc):
    cols = []

    # --- C2DC branch (always compute Ndriz + Nprecip if present) ---
    var_2dc = next((v for v in sizedist_vars if v.startswith('C2DC')), None)
    if var_2dc is not None:
        da, bin_dim, time_name, cells_used, _ = _prep_probe(nc, var_2dc)
        # drizzle: 100–500 µm
        ndriz_2dc = _sum_range_by_upper_edge(da, bin_dim, cells_used, 100.0, 500.0)
        # precip: ≥1000 µm
        nprecip_2dc = _sum_range_by_upper_edge(da, bin_dim, cells_used, 1000.0, None)
        t = pd.to_datetime(da[time_name].values)
        df_2dc = pd.DataFrame({"Ndriz_2DC": ndriz_2dc.values, "Nprecip_2DC": nprecip_2dc.values},index=t)
        df_2dc.index.name = "time"
        cols.append(df_2dc)

    # --- C2DS branch (optional; only Nprecip requested) ---
    var_2ds = next((v for v in sizedist_vars if v.startswith('C2DS') and v.endswith('2H')), None)
    if var_2ds is not None:
        da, bin_dim, time_name, cells_used, _ = _prep_probe(nc, var_2ds)
        nprecip_2ds = _sum_range_by_upper_edge(da, bin_dim, cells_used, 1000.0, None)
        ndriz_2ds = _sum_range_by_upper_edge(da, bin_dim, cells_used, 100.0, 500.0)
        t = pd.to_datetime(da[time_name].values)
        df_2ds = pd.DataFrame({"Ndriz_2DS": ndriz_2ds, "Nprecip_2DS": nprecip_2ds.values}, index=t)
        df_2ds.index.name = "time"
        cols.append(df_2ds)

    # # --- C2DS branch (optional; only Nprecip requested) ---
    var_uhsas = next((v for v in sizedist_vars if v.startswith('CUH')), None)
    if var_uhsas is not None:
        da, bin_dim, time_name, cells_used, _ = _prep_probe(nc, var_uhsas)
        n_accum = _sum_range_by_upper_edge(da, bin_dim, cells_used, 100.0, None)
        n_ait = _sum_range_by_upper_edge(da, bin_dim, cells_used, 70.0, 100.0)
        t = pd.to_datetime(da[time_name].values)
        df_uhs = pd.DataFrame({"Naitk_UH": n_ait, "Naccum_UH": n_accum.values}, index=t)
        df_uhs.index.name = "time"
        cols.append(df_uhs)

    if not cols:
        return pd.DataFrame()

    # time-align and return
    return pd.concat(cols, axis=1).sort_index()

def load_flight_data(dir_path: str, idx: int = 0, add_sizedist: bool = True,
                     asof: bool = False, tol: str = "1s") -> pd.DataFrame:
    """
    High-level loader: base 1 Hz vars + (optional) drizzle/precip from sizedists.
    """    """
    High-Level Function for finding and reading in flight data.

    This function searches a directory for NetCDF (*.nc) flight data files, selects one based on the provided 
    index, opens it, identifies relevant variables based on the dataset contents, and reads those variables 
    into a Pandas DataFrame.

    :param dir_path: Path to the directory containing NetCDF flight data files.
    :param idx: Index of the file to load from the sorted list of *.nc files in the directory.

    :return: A Pandas DataFrame containing the extracted flight data variables.
    """
    flight_dat_paths = find_flight_fnames(dir_path)
    nc = open_nc(flight_dat_paths[idx])
    vars2read = read_vars(nc)
    df = read_flight_nc(nc,vars2read)
    
    # 2) derived from size distributions (returns time-indexed DF)
    sd_vars = read_sizedist_vars(nc)          # your prefix-based picker
    conc_df = calc_concs_from_sd(sd_vars, nc) # columns like Ndriz_2DC, Nprecip_2DC, Nprecip_2DS, ...

    if conc_df is None or conc_df.empty:
        return df

    # 3) join on time
    df2 = df.copy()
    df2["Time"] = pd.to_datetime(df2["Time"]).dt.tz_localize(None).round("S")

    conc = conc_df.copy()
    conc.index = pd.to_datetime(conc.index).tz_localize(None).round("S")

    if asof:
        # nearest match within tolerance (useful if clocks are off by <1s)
        out = pd.merge_asof(
            df2.sort_values("Time"),
            conc.reset_index().rename(columns={"index": "Time"}).sort_values("Time"),
            on="Time",
            direction="nearest",
            tolerance=pd.Timedelta(tol),
        )
    else:
        # exact join on second-resolution timestamps
        out = df2.set_index("Time").join(conc, how="left").reset_index()

    return out


def find_sondes(dir_path: str) -> list[str]:
    """
    find_flight_fnames just searches a directory for all *.nc files and returns a list of them.

    :param dir_path: a path to the directory containing flight netcdf files

    :return: Returns a list of flight netcdf files.
    """
    flight_paths=[]
    flight_fnames = sorted([fname for fname in os.listdir(dir_path) if fnmatch(fname, "*.cls")])
    for i in range(len(flight_fnames)):
        flight_paths.append(dir_path + '/' + flight_fnames[i])
    
    return flight_paths

def read_sonde2df(file_path):
    """
    Reads a `.cls` radiosonde file and extracts multiple datasets with their nominal release times.

    :param file_path: Path to the `.cls` file containing radiosonde data.

    :return: A tuple containing:
        - A list of Pandas DataFrames, each representing an individual radiosonde dataset.
        - A list of corresponding nominal release times as Pandas Timestamps.
    
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the file is incorrectly formatted or missing essential data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    # Read the entire file into memory
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Identify all "Nominal Release Time" occurrences
    start_indices = [i for i, line in enumerate(lines) if "Nominal Release Time" in line]
    
    if not start_indices:
        raise ValueError(f"No 'Nominal Release Time' entries found in file: {file_path}")

    datasets = []
    drop_times = []
    # Process each radiosonde dataset
    for idx, start in enumerate(start_indices):
        # Find the start of the tabular data
        data_start = None
        for i in range(start, len(lines) - 2):
            if lines[i].strip().startswith("Time") and "Press" in lines[i]:  # Detect header row
                data_start = i + 3  # Data starts 2 lines after the column names
                break

        if data_start is None:
            print(f"Warning: No data start found for entry at line {start}")
            continue  # Skip this dataset

        # Extract and convert nominal release time
        try:
            date_time_str = lines[start].split("):")[1].strip()
            drop_time = pd.to_datetime(date_time_str, format='%Y, %m, %d, %H:%M:%S')
        except (IndexError, ValueError) as e:
            print(f"Warning: Failed to parse drop time at line {start}: {e}")
            continue  # Skip this dataset

        drop_times.append(drop_time)

        # Extract column names
        columns = lines[data_start - 3].strip().split()

        # Determine dataset end (next "Nominal Release Time" or end of file)
        end = start_indices[idx + 1] if idx + 1 < len(start_indices) else len(lines)

        # Extract and clean data
        data_lines = [line.strip().split() for line in lines[data_start:end]]
        data = [row for row in data_lines if len(row) == len(columns)]

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=columns)

        if df.empty:
            print(f"Warning: Empty dataset at line {start}")
            continue  # Skip empty datasets

        # Remove rows containing 9999.0 in any column
        df = df[(df != "9999.0").all(axis=1)]
        # Convert numeric columns where possible
        df = df.apply(pd.to_numeric, errors='coerce')
        # Store drop time in DataFrame metadata
        df.attrs["drop_time"] = drop_time
        # Append dataset
        datasets.append(df)

    return datasets

def load_nc_cldrgme(file_paths):

    combined_blocks = []   
    for path in file_paths:
        rf = path.split("/")[-1].split(".")[0]  # e.g., "RF01"
        ds = xr.open_dataset(path)
        
        # Get unique combinations
        labels = ds["block_label"].values
        indices = ds["block_index"].values
        
        # Convert to DataFrame for convenient filtering
        df = ds.to_dataframe().reset_index().drop(columns="index")  # remove redundant index
        
        # Get all unique (label, index) pairs
        unique_blocks = df[["block_label", "block_index"]].drop_duplicates()
        
        # Loop through each unique block
        for _, row in unique_blocks.iterrows():
            label = row["block_label"]
            idx = row["block_index"]
        
            # Filter DataFrame
            df_block = df[(df["block_label"] == label) & (df["block_index"] == idx)].copy()
        
            # (Optional) add flight ID if you have it
            df_block["block_label"] = label
            df_block["block_index"] = idx
        
            combined_blocks.append(df_block)
        all_blocks = pd.concat(combined_blocks, ignore_index=True)
    return all_blocks
# if __name__ == "__main__":
#     inform_utils.()
