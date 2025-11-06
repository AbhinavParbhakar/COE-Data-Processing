import argparse
from auth_provider import AuthProvider
from miovision_info_provider import MiovisionInfoProvider
from report_downloads_provider import DownloadsProvider
from dataclasses import dataclass

@dataclass
class CommandLineArguments:
    miovision_username:str
    miovision_password:str
    auth_session_file_path:str
    miovision_base_folder:str
    start_year:str
    end_year:str
    time_interval:str
    
    def __post_init__(self):
        if not self.start_year.isdigit() or not self.end_year.isdigit():
            raise ValueError("Start Year and End Year must both digits")
        
        if int(self.end_year) < int(self.start_year):
            raise ValueError("Start year must be before end year")
        
        if '.json' not in self.auth_session_file_path:
            raise ValueError("auth_session_file_path must be in the following format '[path].json'")

def configure_parser(arguments:list[str])->argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
    prog="Miovision Scraper",
    description="Downloads all Miovision studies in the specified time range"
    )
    
    for arg in arguments:
        parser.add_argument(arg)    
    return parser


if __name__== '__main__':
    arguments = [
        'miovision_username',
        'miovision_password',
        'auth_session_file_path',
        'miovision_base_folder',
        'start_year',
        'end_year',
        'time_interval'
    ]
    parser = configure_parser(arguments)
    args : dict[str,str] = vars(parser.parse_args())
    
    arguments = CommandLineArguments(
            miovision_username = args['miovision_username'],
            miovision_password = args['miovision_password'],
            auth_session_file_path = args['auth_session_file_path'],
            miovision_base_folder = args['miovision_base_folder'],
            start_year = args['start_year'],
            end_year = args['end_year'],
            time_interval = args['time_interval']
    )

    
    auth = AuthProvider(username=arguments.miovision_username,
                        password=arguments.miovision_password,
                        auth_file_name=arguments.auth_session_file_path)
    
    miovision_info = MiovisionInfoProvider(auth_context_file_name=arguments.auth_session_file_path,
                                           start_year=int(arguments.start_year),
                                           end_year=int(arguments.end_year))
    
    auth.create_authentication_context_session()
    miovision_info = miovision_info.get_miovision_study_types_ids()
    
    downloader = DownloadsProvider(auth_context_file_name=arguments.auth_session_file_path,
                                   folder_path=arguments.miovision_base_folder,
                                   miovision_studies_types_ids=miovision_info,
                                   time_interval=arguments.time_interval)
    
    downloader.download_files()