import pandas as pd
import os
import tqdm

ROWS_SKIPPED_BEFORE_READING_TXT_FILE = 15
ROWS_SKIPPED_SPECIAL_FILE = 14
MAX_METADATA_ROW_NUM = 13
BLACKCAT_DIRECTORY_NAME = './Associated Files/Blackcat 2025/'

def scrape_study(study_path)->pd.DataFrame:
    """
    Given the path to the study, scrape relevant information
    
    ### Parameters
    1. study_path : ``str``
        - Path to an individual file
    
    ### Returns
    A ``pd.DataFrame`` object containing information for specifically a single blackcat study.
    """
    
    keys_list = []
    values_list = []
    directions_set = {'EB','SB','WB','NB'}
    lane_direction_mapping = dict()
    
    # Have to check for 'new' because of ONE FILE that has a different heading arrangement
    if 'New' in study_path or 'NEW' in study_path:
        df = pd.read_csv(study_path,skiprows=ROWS_SKIPPED_BEFORE_READING_TXT_FILE)
        date_col_name = 'Date'
        lane_column_name = ' Channel'
        df[date_col_name] = df.index
    else:
        df = pd.read_csv(study_path,skiprows=ROWS_SKIPPED_SPECIAL_FILE,sep=' ')
        date_col_name = 'Date'
        lane_column_name = 'Lane'
    
    direction_col_name = 'Direction'
    

    
    with open(study_path,mode='rt') as f:
        next(f) # Skip first line, do not need to read the file name
        for i in range(MAX_METADATA_ROW_NUM):
            metadata = f.readline().rstrip()
            information_split =  metadata.split(': ')
            assert information_split.__len__() == 2, f"Metadata not in the format <Key>:<Value> for {study_path}"
            key = information_split[0]
            value = information_split[1]
            
            if key in directions_set:
                # In this case, the value will be the lane number that is referenced in the data columns
                # As such, store the value as the key, and the key (direction) as the mapping
                # So that we can revert later
                
                # SAME THING, checking for new smh
                if 'New' in study_path or 'NEW' in study_path:
                    lane_direction_mapping[f' Lane {value}'] = key
                else:
                    lane_direction_mapping[value] = key
            else:
                keys_list.append(key)
                values_list.append(value)
    
    # Map directions
    assert lane_column_name in df.columns, f'Col "{lane_column_name}" not found in file.'
    df[direction_col_name] = df[lane_column_name].map(lane_direction_mapping)
    
    # Group data based on Date and Direction
    try:
        aggregate_count_df = df.groupby([date_col_name,direction_col_name],as_index=False)[[lane_column_name]].count()
        aggregate_count_df = aggregate_count_df.rename({lane_column_name:'Traffic Count'},axis=1)
    except KeyError as e:
        print(f'File {study_path} caused an error')
        raise e
    
    for i,key in enumerate(keys_list):
        aggregate_count_df[key] = pd.Series([values_list[i]] * aggregate_count_df.shape[0])

    return aggregate_count_df

def aggregate_blackcat(folder_path:str)->pd.DataFrame:
    """
    Given the folder path, return a dataframe containing pertinent information
    
    ### Parameters
    1. folder_path : ``str``
        - Path of directory containing blackcat data.
    
    ### Returns
    A ``pd.DataFrame`` object containing rows representing traffic count per direction per study.
    """
    file_names : list[str] = []
    study_dataframes_list = []
    
    for dirpath, dirnames,filnames in os.walk(folder_path):
        file_names.extend([f'{dirpath}{name}' for name in filnames])
    
    for study_path in tqdm.tqdm(file_names):
        study_dataframes_list.append(scrape_study(study_path=study_path))
        
    
    return pd.concat(study_dataframes_list,ignore_index=True)
    

if __name__ == "__main__":
    df = aggregate_blackcat(folder_path=BLACKCAT_DIRECTORY_NAME)
    df.to_excel('./Associated Files/Blackcat Aggregate Counts.xlsx',index=False)