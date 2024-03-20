"""
 CISCO DataMiner Support Libary

 Auther:  Donnie Savage, 2022
 Derived work from: Steve Hartman, Cisco Systems, INc

"""
import sys
import os
import time
import math
import re
import logging
import shutil
import requests

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.exceptions import Timeout
from requests.packages.urllib3.util.retry import Retry
'''
    Data need by function - must be set by importer
=======================================================================
'''
token = None				# Used for Making API Requests
tokenStartTime = 0			# Tracks time the token was created
tokenUrl = None				# Full path of oAuth endpoint: <protocolscheme><host><path>

authScope = None			# # Specify the access level or permissions. Default is None
grantType = None			# Grant Type being used - defalt: client_credentials
clientId = None				# Used to store the Client ID
clientSecret = None			# Used to store the Client Secret
grantType = "client_credentials"	# Grant Type being used - defalt: client_credentials
cacheControl = "no-cache"		# By default, dont cache
urlTimeout = 10				# Second to wait for the api to respond default = 10

'''
Begin defining functions neeed to support PXC and SNTC DataMiners
=======================================================================
'''
# Function to generate or clear output and temp folders for use.
def storage(csv_dir=None, json_dir=None, temp_dir=None):

    # Output CSV
    if csv_dir:
        if os.path.isdir(csv_dir):
            shutil.rmtree(csv_dir)
            os.mkdir(csv_dir)
        else:
            os.mkdir(csv_dir)

    # Output JSON
    if json_dir:
        if os.path.isdir(json_dir):
            shutil.rmtree(json_dir)
            os.mkdir(json_dir)
        else:
            os.mkdir(json_dir)

    # Temp dir for download data
    if temp_dir:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
            os.mkdir(temp_dir)
        else:
            os.mkdir(temp_dir)

#
# Fix file name to be Windows compatable
def filename(filename):
    # Define a pattern to match characters not allowed in Windows filenames
    invalid_char_pattern = re.compile(r'[<>:"/\\|?* &\x00-\x1F]+')

    # Replace invalid characters with an underscore
    name = invalid_char_pattern.sub('_', filename)
    return name

#
# JSON Naming Convention: <page_name>_Page_{page}.json
def pagename(page_name, page):
    page = page_name + "_Page_" + str(page) + ".json"
    return filename(page)

#
# JSON Naming Convention: <page_name>_Page_{page}_of_{total}.json
def pageofname(page_name, page, total):
    page = page_name + "_Page_" + str(page) + "_of_" + str(total) + ".json"
    return filename(page)

#
# common error handling
def api_exception(e):
    logging.warning(f"Exception:{e}")
    if hasattr(e, 'request') and e.request:
        # Logging.Info details of the request that caused the exception
        logging.error(f"{e.request.method} Request URL: {e.request.url}")
        logging.debug(f"Request Headers{e.request.headers}")
        logging.debug(f"Request Body:{e.request.body}")

    if hasattr(e, 'response') and e.response:
        logging.error(f"Response Status Code:{e.response.status_code}")
        logging.debug(f"Response Headers:{e.response.headers}")
        logging.debug(f"Response Content:{e.response.text}")

#
# try to figure out the HTTP error - in the case of some exceptions, the response is not provied,
# so we have to look at the error sting to see if we can figure it out
def api_exception_code(e):
    http_status_code_pattern = re.compile(r'\b(\d{3})\b')

    if hasattr(e, 'response') and e.response:
        return e.response.status_code

    else:
        # Search for the pattern in the string
        code = http_status_code_pattern.search(str(e))

        # Return the matched HTTP status code or None if not found
        return int(code.group(1)) if code else None

#
# handle the send
def api_header():
    header = {'Authorization': f'Bearer {token}'}
    return header
#
# function to contain the error logic for any API request call
def api_request(method, url, header, **kwargs):
    firstTime = True
    tries = 1
    response = []

    # Include all HTTP error codes (4xx and 5xx) in status_forcelist
    all_error_codes = [code for code in range(400, 600)]

    # Create a custom Retry object with max retries
    retry_strategy = Retry(
        total=30,		# Maximum number of retries
        backoff_factor=0.1,	# Factor to apply between retry attempts
        status_forcelist=all_error_codes,
    )
    
    # Create a custom HTTPAdapter with the Retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # Create a Session and mount the custom adapter
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    # Rather Chatty ...
    logging.debug(f"{method}: URL:{url}")
    while True:
        try:
            response = requests.request(method, url, headers=header, verify=True, timeout=urlTimeout, **kwargs)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

            status_code = response.status_code
            if response.status_code == 200:
                if tries >= 2:
                    logging.info("\nSuccess on retry! \nContinuing.")
                break
        except Timeout as e:
            logging.warning(f"Timeout: Method:{method} Attempt:{tries}")
            api_exception(e)
            time.sleep(1)
        except requests.exceptions.HTTPError as e:
            status_code = api_exception_code(e)
            logging.error(f"HTTPError: Status:{status_code} Method:{method} Attempt:{tries}")
            api_exception(e)

            if status_code >= 500:
                logging.info("Server Error: Retrying: {e}")
            elif status_code == 401:
                if firstTime:
                    logging.error(f"HTTPError 401 Retrying: {e}")
                    token_get()			# Maybe expired - get new token
                    header = api_header()	# New token needs new header
                    firstTime = False
                else:
                    logging.error(f"HTTPError 401 Aborting: {e}")
                    return status_code, response
            elif status_code == 400:
                logging.error(f"HTTPError 400 Aborting: {e}")
                return status_code, response
            elif status_code == 403:
                logging.error(f"HTTPError 403 Aborting: {e}")
                return status_code, response
            else:
                logging.error(f"HTTPError:{status_code}  Attempt:{tries}")

        except requests.exceptions.RequestException as e:
            logging.warning(f"RequestException: Method:{method} Attempt:{tries}")
            api_exception(e)
        except requests.exceptions.ReadTimeout as e:
            logging.warning(f"ReadTimeoutError: Method:{method} Attempt:{tries}")
            api_exception(e)
        except requests.exceptions.Timeout as e:
            logging.warning(f"TimeoutError: Method:{method} Attempt:{tries}")
            api_exception(e)
        except ConnectionError as e:
            logging.warning(f"ConnectionError: Method:{method} Attempt:{tries}")
            api_exception(e)
        except Exception as e:
            logging.warning(f"Unexpected error: Method:{method} Attempt:{tries}")
            api_exception(e)
        finally:
            tries += 1
            time.sleep(2)		# 2 seconds delay before the next attempt

        #End Try
    #End While
    return response.status_code, response

# If needed, refresh the token so it does not expire
def token_refresh(max_time=100):
    checkTime = time.time()
    tokenTime = math.ceil(int(checkTime - tokenStartTime) / 60)
    if tokenTime > max_time:
        logging.info(f"Token Time is :{tokenTime} minutes, Refreshing")
        token_get()
    else:
        logging.debug(f"Token time is :{tokenTime} minutes")


# Function to get a valid API token from PX Cloud
def token_get():
    global token
    global tokenStartTime

    print("\nGetting API Access Token")
    url = (tokenUrl
           + "?grant_type="    + grantType
           + "&client_id="     + clientId
           + "&client_secret=" + clientSecret
           + "&cache-control=" + cacheControl
    )

    # if scope is needed, add it now
    if authScope:
        url += "&scope=" + authScope

    header = {'Content-type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, headers=header)
    if response:
        reply = response.json()
        token = reply.get("access_token", None)
    else:
        token = None
        
    tokenStartTime = time.time()
    logging.debug(f"API Token:{token}")
    if token:
        print("Done!")
        print("====================")

    else: 
        logging.critical("Unable to retrieve a valid token\n"
              "Check config.ini and ensure your API Keys and if your using the Sandbox or Production for accuracy")
        logging.critical(f"Client ID: {clientId}")
        logging.critical(f"Client Secret: {clientSecret}")
        sys.exit()



