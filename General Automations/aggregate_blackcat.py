import pandas as pd
import os

ROWS_SKIPPED_BEFORE_READING_TXT_FILE = 15
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
    
    information_dict = {}
    
    
    with open(study_path,mode='rt') as f:
        next(f) # Skip first line, do not need to read the file name
        row_index = 0
        while row_index < MAX_METADATA_ROW_NUM:
            metadata = f.readline().rstrip()
            information_split =  metadata.split(': ')
            assert information_split.__len__() == 2, "Metadata not in the format <Key>:<Value>"
            key = information_split[0]
            value = information_split[1]
            information_dict[key] = value
            
            row_index +=1

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
    
    for study_path in file_names:
        study_dataframes_list.append(scrape_study(study_path=study_path))
        
    
    return pd.concat(study_dataframes_list,ignore_index=True)
    

if __name__ == "__main__":
    df = aggregate_blackcat(folder_path=BLACKCAT_DIRECTORY_NAME)
    df.to_excel('./Associated Files/Blackcat Aggregate Counts.xlsx',index=False)