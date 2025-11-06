from playwright.sync_api import sync_playwright, Playwright, Page, BrowserContext
from dataclasses import dataclass
from dotenv import dotenv_values
import logging
import datetime
import os
from google.cloud import storage
from google.cloud.exceptions import Conflict
import io
from typing import cast, TextIO

# Gobal Variables
MAX_AUTH_DEFAULT_NAV_TIMEOUT = 60000 # miliseconds
MAX_MIOVISION_ID_MAX_DEFAULT_NAVIGATION_TIMEOUT = 90000# milliseconds
MIOVISION_SCREENSHOT_MAX_LOCATOR_TIMEOUT = 240000 #milliseconds
SCRAPING_START_YEAR = int(os.environ.get('SCRAPING_START_YEAR', 2024))
SCRAPING_END_YEAR = int(os.environ.get('SCRAPING_END_YEAR', 2024))

def configure_logging()->logging.Logger:
    """
    Configure logging
    
    ### Returns
    logger with configuration set up
    """
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f"{__name__}.log",level=logging.INFO,filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    return logger

@dataclass
class ConfigurationDetails:
        
    AUTH_FILE_NAME : str
    AUTH_USERNAME : str
    AUTH_PASSWORD : str
    AUTH_LINK : str
    AUTH_MAX_DEFAULT_NAVIGATION_TIMEOUT : int
    AUTH_USERNAME_LOCATOR : str
    AUTH_SUBMIT_USERNAME_BUTTON_LOCATOR : str
    AUTH_PASSWORD_LOCATOR : str
    AUTH_SUBMIT_PASSWORD_BUTTON_LOCATOR : str
    
    SCRAPING_START_YEAR : int
    SCRAPING_END_YEAR : int
    
    MIOVISION_ID_LOCATOR : str
    MIOVISION_TOTAL_COUNT_VALIDTION_LOCATOR : str
    MIOVISION_ID_MAX_DEFAULT_NAVIGATION_TIMEOUT : int
    MIOVISION_SCREENSHOTS_FOLDER_NAME : str
    MIOVISION_SCREENSHOT_LOCATOR : str
    MIOVISION_SCREENSHOT_MAX_LOCATOR_TIMEOUT : int
    MIOVISION_GREEN_SYMBOL_LOCATOR : str
    MIOVISION_SOUND_SYMBOL_LOCATOR : str
    
    CLOUD_BUCKET_NAME : str

class AuthProvider():
    def __init__(self,username:str,password:str,auth_file_name:str) -> None:
        pass

class URLsProvider():
    def __init__(self,auth_file_name:str,scraping_start_year:int,scraping_end_year:int) -> None:
        config = dotenv_values(".env")
        
        auth_file_name_env_key = 'AUTH_FILE_NAME'
        auth_username_env_key = 'USERNAME'
        auth_password_env_key = 'PASSWORD'
        auth_link_env_key = 'AUTH_LINK'
        
        
        if auth_file_name_env_key not in config:
            raise(Exception(f"{auth_file_name_env_key} key not found in .env file"))
        
        if auth_password_env_key not in config:
            raise(Exception(f"{auth_password_env_key} key not found in .env file"))
        
        if auth_link_env_key not in config:
            raise(Exception(f"{auth_link_env_key} key not found in .env file"))
            
            
        
        auth_username_locator = 'input[name="username"]'
        miovision_validation_locator = 'div.text-center'
        auth_username_submit_button_locator = 'button[type="submit"]'
        auth_password_locator = 'input[name="password"]'
        auth_password_submit_button_locator = 'button[type="submit"]'
        miovision_id_locator = 'tr[class="marker_hover"] >> div.miogrey'
        miovision_screenshots_folder_name = "Screenshots"
        miovision_screenshot_locator = 'button.gm-control-active.gm-fullscreen-control'
        miovision_green_symbol_locator = 'xpath=//div[contains(@style, "width: 48px") and contains(@style, "height: 68px")]'
        miovision_sound_symbol_locator = 'xpath=//div[(contains(@style, "width: 58px") and contains(@style, "height: 58px")) or (contains(@style, "width: 56px") and contains(@style, "height: 57px"))]'
        cloud_bucket_name = 'miovision_urls_bucket'
        
        auth_config = ConfigurationDetails(
            AUTH_FILE_NAME = str(config[auth_file_name_env_key]),
            AUTH_USERNAME = str(config[auth_username_env_key]),
            AUTH_PASSWORD = str(config[auth_password_env_key]),
            AUTH_LINK = str(config[auth_link_env_key]),
            AUTH_MAX_DEFAULT_NAVIGATION_TIMEOUT = MAX_AUTH_DEFAULT_NAV_TIMEOUT,
            AUTH_USERNAME_LOCATOR = auth_username_locator,
            AUTH_SUBMIT_USERNAME_BUTTON_LOCATOR = auth_username_submit_button_locator,
            AUTH_PASSWORD_LOCATOR = auth_password_locator,
            AUTH_SUBMIT_PASSWORD_BUTTON_LOCATOR = auth_password_submit_button_locator,
            SCRAPING_START_YEAR = SCRAPING_START_YEAR,
            SCRAPING_END_YEAR = SCRAPING_END_YEAR,
            MIOVISION_ID_LOCATOR = miovision_id_locator,
            MIOVISION_ID_MAX_DEFAULT_NAVIGATION_TIMEOUT = MAX_MIOVISION_ID_MAX_DEFAULT_NAVIGATION_TIMEOUT,
            MIOVISION_SCREENSHOTS_FOLDER_NAME = miovision_screenshots_folder_name,
            MIOVISION_SCREENSHOT_LOCATOR = miovision_screenshot_locator,
            MIOVISION_SCREENSHOT_MAX_LOCATOR_TIMEOUT = MIOVISION_SCREENSHOT_MAX_LOCATOR_TIMEOUT,
            MIOVISION_GREEN_SYMBOL_LOCATOR = miovision_green_symbol_locator,
            MIOVISION_SOUND_SYMBOL_LOCATOR = miovision_sound_symbol_locator,
            CLOUD_BUCKET_NAME = cloud_bucket_name,
            MIOVISION_TOTAL_COUNT_VALIDTION_LOCATOR = miovision_validation_locator
        )
        
        logger = configure_logging()
        
        main(config=auth_config,logger=logger)
    
    def create_auth_credentials(playwright:Playwright, config: ConfigurationDetails,logger:logging.Logger)->None:
        """
        Automates the process of generating a auth json config file using the name
        provided in the config object.
        
        ### Parameters
        1. playwright: ``Playwright``
            - Used to access the browser for automation
        2. config: ``ConfigurationDetails``
            - Contains information for populating details on the authentication page
        3. logger: ``logging.Logger``
            - Logger object used for logging
        
        ### Effects
        Started a headless automation of chromium for the link provided
        
        ### Returns
        None
        """
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        context.set_default_navigation_timeout(config.AUTH_MAX_DEFAULT_NAVIGATION_TIMEOUT)
        page = context.new_page()
        
        logger.info("[create_auth_credentials]: Started navigation to auth link")
        page.goto(config.AUTH_LINK)
        
        # Input and submit username
        logger.info("[create_auth_credentials]: Started completion of username")
        page.locator(config.AUTH_USERNAME_LOCATOR).type(config.AUTH_USERNAME)
        page.locator(config.AUTH_SUBMIT_USERNAME_BUTTON_LOCATOR).first.click()
        
        # Input and submit password
        logger.info("[create_auth_credentials]: Started completion of password")
        page.locator(config.AUTH_PASSWORD_LOCATOR).type(config.AUTH_PASSWORD)
        page.locator(config.AUTH_SUBMIT_PASSWORD_BUTTON_LOCATOR).first.click()
        
        # Wait for page load
        logger.info("[create_auth_credentials]: Waiting for load state")
        page.wait_for_load_state()

        # Saving auth details
        logger.info("[create_auth_credentials]: Saved auth details")
        context.storage_state(path=config.AUTH_FILE_NAME)
        
        # Clean up
        logger.info("[create_auth_credentials]: Closing page, context, and browser")
        page.close()
        context.close()
        browser.close()

    def check_date_pattern(date_string:str)->bool:
        """
        Check if the date matches YYYY-MM-DD
        ### Parameters
        1. date_string : ``str``
            - String to be compared against the format
            
        ### Returns
        True or False for a valid or invalid pattern, respectively.
        """
        try:
            datetime.datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def retrieve_urls(page:Page,logger:logging.Logger,start_date:str,end_date:str,base_url:str,id_locator:str,validation_locator)->list[str]:
        """
        Given the page, navigate to the base url after adding the start date and end date and return all miovsion urls from the page
        
        ### Parameters
        1. page: ``Page``
            - Page object used for navigation
        2. logger: ``logging.Logger``
            - Used for logging purposes
        3. start_date: ``str``
            - Start date should be provided in 'YYYY-MM-DD'
        4. end_date : ``str``
            - End date should be provided in 'YYYY-MM-DD'
        5. base_url : ``str``
            - Base url upon which the navigation url is built
        6. id_locator : ``str``
            - Element css used to locate the space where the IDs are stored.
        7. validtion_locator : ``str``
            - Element css used to locaate the number of studies per page to validate that each one was extracted
        
        ### Returns
        List of urls stored in ``str`` format
        """
        if not check_date_pattern(start_date) or not check_date_pattern(end_date):
            raise Exception("Dates muste be given in YYYY-MM-DD format")
        
        link = base_url + f'studies/?end_date={end_date}&start_date={start_date}&state=Published'
        
        # Grab all id's after parsing
        logger.info(f'[retrieve_ids] Navigating to {link}')
        page.goto(link)
        
        miovision_total_studies_count_text : str = page.locator(validation_locator).inner_text()
        miovision_total_studies_count : int = int(miovision_total_studies_count_text.split("Studies")[0]) # Text is in the form: "<Count> Studies"
        
        uncleaned_ids = page.locator(id_locator).all_inner_texts()
        cleaned_urls = set()
        
        for id_text in uncleaned_ids:
            # Remove whitespace
            id_text = id_text.strip(' ')
            clean_id = id_text.split("#")[-1]
            cleaned_urls = cleaned_urls.union([f'{base_url}studies/{clean_id}'])
        
        assert len(cleaned_urls) == miovision_total_studies_count, f"Mismatch between extracted studies ({len(cleaned_urls)}) and expected number of studies ({miovision_total_studies_count})."
        logger.info(f'[retrieve_ids] Returning {len(cleaned_urls)} ids')
        return list(cleaned_urls)
        
        
    def scrape_miovision_urls(playwright:Playwright,config:ConfigurationDetails,logger:logging.Logger)->list[str]:
        """
        Using the start and end year values stored in config, scrape the website
        and return the urls for the studies that exist within that temporal window.
        
        ### Parameters
        1. playwright: ``Playwright``
            - Object used for scraping
        2. config: ``ConfigurationDetails``
            - Stores configuration details for scraping
        3. logger: ``logging.Logger``
            - Used for logging
        
        ### Effects
        Starts headless chromium browsers
        
        ### Returns
        List of urls stored as ``str``
        """
        
        start_year = config.SCRAPING_START_YEAR
        end_year = config.SCRAPING_END_YEAR
        
        miovision_ids = list()
        
        logger.info('[scrape_miovision_ids] Starting browser')
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(storage_state=config.AUTH_FILE_NAME)
        context.set_default_navigation_timeout(config.MIOVISION_ID_MAX_DEFAULT_NAVIGATION_TIMEOUT)
        page = context.new_page()
        while start_year <= end_year:        
            for i in range(1,13):
                start_date = f'{start_year}-{i}-01'
                if i == 12:
                    end_date = f'{start_year + 1}-01-01'
                else:
                    end_date = f'{start_year}-{i+1}-01'
                
                logger.info(f'[scrape_miovision_ids] Getting ids from {start_date} to {end_date}')
                try:
                    monthly_ids = retrieve_urls(
                        page=page,
                        logger=logger,
                        start_date=start_date,
                        end_date=end_date,
                        base_url=config.AUTH_LINK,
                        id_locator=config.MIOVISION_ID_LOCATOR,
                        validation_locator=config.MIOVISION_TOTAL_COUNT_VALIDTION_LOCATOR
                    )
                    
                    miovision_ids.extend(monthly_ids)
                except Exception as e:
                    logger.error(f'[scrape_miovision_ids] Error: {e}')
            
            start_year +=1
        
        logger.info("[scrape_miovision_ids] Closing page, context, and browser")
        page.close()
        context.close()
        browser.close()
        return miovision_ids  

    def send_urls_files_to_cloud_storage(urls:list[str],config:ConfigurationDetails,logger:logging.Logger)->None:
        url_text_stream = io.BytesIO()
        url_text_stream.writelines([url.encode() + b'\n' for url in urls])
        url_text_stream.seek(0)
        
        logger.info('[send_urls_files_to_cloud_storage] Starting transfer to bucket')    
        storage_client = storage.Client()
        try:
            storage_client.create_bucket(bucket_or_name=config.CLOUD_BUCKET_NAME,location='US-CENTRAL1')
        except Conflict:
            logger.warning(f'[send_urls_files_to_cloud_storage] Bucket {config.CLOUD_BUCKET_NAME} already exists. ')
        bucket = storage_client.bucket(config.CLOUD_BUCKET_NAME)
        
        file_blob = bucket.blob("miovision_urls.txt")
        file_blob.upload_from_file(url_text_stream)
        
        logger.info('[send_urls_files_to_cloud_storage] Finished writing to bucket')    
        
        # with cast(TextIO,file_blob.open(mode='wt')) as writer:
        #     writer.writelines([f'{url}\n' for url in urls])
        
            
    def main(config:ConfigurationDetails,logger:logging.Logger):
        """
        Main method to orchestrate the flow of execution
        
        ### Parameters
        1. config: ``ConfigurationDetails``
            - Data class that contains details for configuration
        2. logger: ``logging.Logging``
            - Logger object used for logging
            
        ### Effects
        Starts the flow of extracting auth details and scraping
        
        ### Returns
        None
        """
        with sync_playwright() as playwright:
            logger.info("Started subroutine for auth credentials generation.")
            create_auth_credentials(playwright=playwright,config=config,logger=logger)
            miovision_urls = scrape_miovision_urls(playwright=playwright,config=config,logger=logger)
            send_urls_files_to_cloud_storage(miovision_urls,config=config,logger=logger)

    if __name__ == "__main__":
        