import pandas as pd
import os
import tqdm

STORAGE_DIRECTORY = './Associated Files/NC 2025/'
LOCATION_FILE_NAME = 'NC - Location Coordinates'
ROWS_SKIPPED_BEFORE_COLUMNS = 10

def return_lat_long(study_name:str,location_df:pd.DataFrame)->tuple[float,float]:
    """
    Given the study name and location names df, match the study name to closest location name based on jaccard similarity and return
    the lat and long stored in the location_df object. 
    
    ### Parameters
    1. study_name : ``str``
        - Name of the study 
    2. location_df : ``pd.DataFrame``
        - Object containing geocodes for all of the studies
    
    ### Effects
    Nothing outside of this function.
    
    ### Returns
    A ``tuple(float,float)`` object returning the (latitude,longitude).
    """
    
    study_name_set = {word for word in study_name.split(' ')}
    
    location_name_col = 'LocationName'
    lat_col_name = 'NC_Latitude'
    long_col_name = 'NC_Longitude'
    
    location_names : list[str] = location_df[location_name_col].tolist()
    location_sets = [{word for word in location_name.lower().split(' ')} for location_name in location_names]
    
    # Jaccard similarity: len(intersection of sets) / len(union of sets)
    jaccard_scores = [len(location_set.intersection(study_name_set)) / len(location_set.union(study_name_set)) for location_set in location_sets]
    max_jaccard_score = max(jaccard_scores)
    max_jaccard_index = jaccard_scores.index(max_jaccard_score)
    
    return location_df.loc[max_jaccard_index,lat_col_name], location_df.loc[max_jaccard_index,long_col_name]
    

def scrape_information_per_file(study_file_path:str, geocode_file_path:str)->pd.DataFrame:
    """
    Given the study_file_path, scrape relevant information and use in tandem with geocode_file_path file to attach lat and long
    and output dataframe containing count information.
    
    ### Parameters
    1. study_file_path : ``str``
        - Path to file containg information on the study
    2. geocode_file : ``str``
        - Path to file containing location information.
        
    ### Effects
    Nothing outside of this function

    ### Returns
    A ``pd.DataFrame`` containing all counts grouped by day for the study.
    """
    
    study_df = pd.read_excel(study_file_path)
    study_data_df = pd.read_excel(study_file_path,skiprows=ROWS_SKIPPED_BEFORE_COLUMNS)
    locations_df = pd.read_excel(geocode_file_path)
    
    information_dict = {}
    
    # Get count per day, name of day, and date
    grouping_col_name = 'Date And Time'
    count_col_name = 'Count'
    assert grouping_col_name in study_data_df.columns, ValueError('Column "Date And Time" not found in study. Check the value assigned for ROWS_SKIPPED_BEFORE_COLUMNS')
    assert count_col_name in study_data_df.columns, ValueError('Column "Count" not found in study. Check the value assigned for ROWS_SKIPPED_BEFORE_COLUMNS')
    
    # Create a DateTimeIndex so that it can be used for grouping
    study_data_df = study_data_df[~study_data_df[grouping_col_name].isna()]
    study_data_df[grouping_col_name] = pd.to_datetime(study_data_df[grouping_col_name])
    study_data_df = study_data_df.set_index(grouping_col_name)
    
    aggregated_counts_series = study_data_df.groupby(pd.Grouper(grouping_col_name,freq='1D'))[count_col_name].count()
    
    information_dict['Date'] = aggregated_counts_series.index.strftime('%Y-%m-%d')
    information_dict['Day of Week'] = aggregated_counts_series.index.day_name()
    information_dict[count_col_name] = aggregated_counts_series.values
    
    # Get study Name
    study_name_col = study_df.columns[4]
    study_label_col = study_df.columns[1]
    study_label_target = 'Street:'
    study_name_row_index = study_df[study_name_col][study_df[study_label_col] == study_label_target].index
    study_name : str = study_df.loc[study_name_row_index,study_name_col].tolist()[0]
    
    # Get the latitude and longitude
    latitude, longitude = return_lat_long(study_name=study_name,location_df=locations_df)
    
    # Split the file name to remove the extension and then split by white space to get the last word (representing the direction)
    direction_name = study_file_path.split('.')[1].split(' ')[-1].upper()
    
    information_dict['Name'] = [study_name] * len(aggregated_counts_series)
    information_dict['Latitude'] = [latitude] * len(aggregated_counts_series)
    information_dict['Longitude'] = [longitude] * len(aggregated_counts_series)
    information_dict['Direction'] = [direction_name] * len(aggregated_counts_series)
    
    return pd.DataFrame(information_dict)
    

def aggregate_NC_files(folder_path:str, location_file_name:str)->pd.DataFrame:
    """
    Given the file path to the NC directory, read through every file and scrape up relevant details
    
    ### Parameters
    1. folder_path : ``str``
        - Path to storage (relative or absolute)
    2. location_file_name : ``str``
        - Name of the file which contains the geocodes for each of the locations in the directory
    
    ### Effects
    Nothing outside of this function.
    
    ### Returns
    A ``pd.DataFrame`` object containing the aggregated information.
    """
    
    file_addresses : list[str] = []
    location_file_address = ''
    location_file_index = -1
    
    for dirpath, dirnames, filenames in  os.walk(folder_path):
        file_addresses.extend([dirpath + filename for filename in filenames])
        
        # Obtain the address for the geocode file
        for i,address in enumerate(file_addresses):
            if location_file_name in address:
                location_file_address = address
                location_file_index = i
        
    if location_file_index == -1:
        raise Exception("Geocode file not found in the directory")
    else:
        # Delete the location file from list of files representing studies
        file_addresses.pop(location_file_index)
    
    study_dataframes_list : list[pd.DataFrame] = []
    
    for address in tqdm.tqdm(file_addresses):
        study_dataframes_list.append(scrape_information_per_file(study_file_path=address,geocode_file_path=location_file_address))
        
    return pd.concat(study_dataframes_list,ignore_index=True)

if __name__ == "__main__":
    df = aggregate_NC_files(folder_path=STORAGE_DIRECTORY,location_file_name=LOCATION_FILE_NAME)
    df.to_excel('./Associated Files/NC Aggregate Counts.xlsx',index=False)