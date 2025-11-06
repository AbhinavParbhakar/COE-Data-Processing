from dataclasses import dataclass
from logger_provider import configure_logging
import os
import json
import io
import requests
import pandas as pd

@dataclass
class DownloadsConfig:
    AUTH_CONTEXT_FILE_NAME:str
    TIME_INTERVAL:int
    BASE_FOLDER_PATH:str

class DownloadsProvider:
    """
    Downloads the excel reports for the following studies with the requested time granularity.
    Expects the list passed in to be contain ``(<Study Type : str>,<Study ID : str>)`` for each element.
    """
    def __init__(self, auth_context_file_name:str, folder_path:str, miovision_studies_types_ids:list[tuple[str,str]], time_interval:str) -> None:
        time_interval_mapping = {
            '1 minute' : 60,
            '5 minutes' : 300,
            '10 minutes' : 600,
            '30 minutes' : 1800,
            '1 hour' : 3600
        }
        
        if time_interval not in time_interval_mapping:
            raise ValueError(f"time_interval must be one of {list(time_interval_mapping.keys())}")
        
        self.logger = configure_logging(logger_name="DownloadsProvider")
        
        self.miovision_info = miovision_studies_types_ids
        self.config = DownloadsConfig(
            AUTH_CONTEXT_FILE_NAME=auth_context_file_name,
            TIME_INTERVAL=time_interval_mapping[time_interval],
            BASE_FOLDER_PATH=folder_path
        )
    
    def download_files(self)->None:
        if not os.path.exists(self.config.BASE_FOLDER_PATH):
            os.mkdir(self.config.BASE_FOLDER_PATH)
        
        auth_file = open(self.config.AUTH_CONTEXT_FILE_NAME)
        auth_credentials : dict = json.loads(auth_file.read())
        auth_file.close()
        headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "cookie": f"central_production_session_id={auth_credentials['cookies'][0]['value']}; return_to=https://datalink.miovision.com/studies?end_date=2023-09-30&start_date=2023-09-01; intercom-device-id-mi3ti0da=3fd9cefa-c2a6-4b36-8774-30be6acd47a0; intercom-session-mi3ti0da=TXBVR3lWTmErNFRtWWFhTEZSYy93SGJacVNFMVlIaVJiR2ZtblRadWxyYXF5NC9RSXc4UThCS3lYVnQ1SnVHLy0tRmg5UFhvWExvbVV2ejhjVGJtMndXZz09--c5a252b23a20dd34264913de39638c846f16f6e8; download_token_1727916324=1727916324",
        "Referer": "https://datalink.miovision.com/studies/1127843",
        "Referrer-Policy": "strict-origin-when-cross-origin"}
        url = 'https://datalink.miovision.com/studies/{study_id}/report?download_token=1727917620&report%5Bformat%5D=xlsx&report%5Bbin_size%5D={time_interval}&report%5Bworksheet_grouping%5D=by_direction&report%5Bapproach_order%5D=n_ne_e_se_s_sw_w_nw&report%5Binclude_raw_data%5D=false&report%5Bforced_peak_enabled%5D=false'
        
        for study_type, study_id in self.miovision_info:
            try:
                response = requests.get(url=url.format(study_id=study_id,time_interval=str(self.config.TIME_INTERVAL)),
                                        headers=headers)
                
                if response.status_code != 200:
                    raise Exception(f"Response code for API request expected to be 200, received {response.status_code}")
                with open(f'{self.config.BASE_FOLDER_PATH}/{study_type}-{study_id}.xlsx',mode='wb') as f:
                    f.write(io.BytesIO(response.content).getbuffer())
                self.logger.info(f'[download_files] Report downloaded for study {study_id}')
            except Exception as e:
                self.logger.error(f'[download_files] Error occured for study {study_id}: {e}')