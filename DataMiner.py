#
#
# adding Cisco DataMiner Module system path
import sys
import os
import shutil
import csv
import time
import sys
import math
import random
import logging
import json

import time
from datetime import datetime

import argparse
from configparser import ConfigParser

import requests
from requests.exceptions import Timeout

import cdm
from cdm import token
from cdm import tokenStartTime
from cdm import tokenUrl
from cdm import grantType
from cdm import clientId
from cdm import clientSecret
from cdm import cacheControl
from cdm import authScope
from cdm import urlTimeout

# Cisco DataMiner Module Variables
# =======================================================================
cdm.tokenUrl = 'https://id.cisco.com/oauth2/default/v1/token'
cdm.clientId = ''
cdm.clientSecret = ''
cdm.urlTimeout = 0
calls_per_sec = 3

# SNTC debugging settings
# =======================================================================
# Generic URL Variables
baseUrl = ''
urlProtocol = "https://"
urlHost = "api-cx.cisco.com/"
urlLink = ''
environment = ''

# File Variables
configFile = 'config.ini'

# Define a mapping of log level strings to logging levels
DEBUG	 = 'DEBUG'
INFO	 = 'INFO'
WARNING  = 'WARNING'
ERROR	 = 'ERROR'
CRITICAL = 'CRITICAL'

# Debug Variables
debug = 0
log_levels = {
    DEBUG: logging.DEBUG,
    INFO: logging.INFO,
    WARNING: logging.WARNING,
    ERROR: logging.ERROR,
    CRITICAL: logging.CRITICAL
}
log_level = INFO

# Data File Variables
sntc_dir = '../'
log_output_dir = 'outputlog/'
csv_output_dir = 'outputcsv/'
json_output_dir = 'outputjson/'
temp_dir = 'temp/'

# Logging Variables
fmt = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
logfile = 'SNTC_DataMiner_log.txt'

# Debug Variables
codeVersion = str("2.0.0-d")
scope = '1'
customerID = 0
debug = 0
testLoop = 0

'''
Begin defining functions
=======================================================================
'''
def init_logger(level, verbose):
    global log_level

    # Check if the specified log level is valid
    #   CRITICAL: Indicates a very serious error, typically leading to program termination.
    #   ERROR:    Indicates an error that caused the program to fail to perform a specific function.
    #   WARNING:  Indicates a warning that something unexpected happened
    #   INFO:     Provides confirmation that things are working as expected
    #   DEBUG:    Provides info useful for diagnosing problems
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        print("Invalid log level. Please use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        exit(1)
    log_level = level

    # Set up logging based on the parsed log level
    log_file = f"{log_output_dir}/{logfile}"
    if verbose:
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler(log_file),
                                logging.StreamHandler()])
    else:
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s',
                            filename=log_file)


def logger(msg_level, *args, **kwargs):
    # Join the arguments into a single string, just like print does
    end = kwargs.pop('end', '\n')
    message = ' '.join(map(str, args))
    
    # Get the logging level based on the custom log level
    logging_value = log_levels.get(msg_level)
    if logging_value is None:
        raise ValueError(f"Invalid log level: {msg_level}")

    # Log the message
    logging.getLogger().log(logging_value, message)

    # Optionally print the message if needed (adjust as per your needs)
    if msg_level == "CRITICAL" or msg_level == "ERROR" or msg_level == log_level:
        print(message, end=end)
       
# Function explain usage
# Function explain usage
def usage():
    print(f"Usage: python3 {sys.argv[0]} <partner> -log=<LOG_LEVEL>")
    print(f"Args:")
    print(f"   Optional named section for partner auth credentials.\n")
    sys.exit()

# Function to load configuration from config.ini and continue or create a template if not found and exit
def load_config(partner):
    global scope
    global customerID
    global debug
    global baseUrl
    global testLoop

    config = ConfigParser()
    if os.path.isfile(configFile):
        print(f'Config.ini file was found, continuing... Loading:{partner}')
        config.read(configFile)

        # check to see if credentials exist for a named partner.
        # default partner config is 'credentials'
        if not partner in config:
            print(f"\nError: Credentials for Partner {partner} not found in config.ini")
            usage()

        # [credentials]
        cdm.clientId = (config[partner]['clientId'])
        cdm.clientSecret = (config[partner]['clientSecret'])

        # [Settings]
        cdm.tokenUrl = (config['settings']['tokenUrl'])
        cdm.urlTimeout = int((config['settings']['urlTimeout']))

        customerID = int((config['settings']['customerID']))
        debug = int((config['settings']['debug']))
        testLoop = int((config['settings']['testLoop']))
        scope = int((config['settings']['scope']))
        baseUrl = (config['settings']['baseUrl'])

        if not cdm.clientId:
            print(f'Missing Credentials for Partner {partner} not found in config.ini')
            sys.exit()
       
    else:
        print('Config.ini not found!!!!!!!!!!!!\nCreating config.ini...')
        print('\nNOTE: you must edit the config.ini file with your information\nExiting...')
        config.add_section('credentials')
        config.set('credentials', 'clientId', 'clientId')
        config.set('credentials', 'clientSecret', 'clientSecret')
        config.add_section('settings')
        config.set('settings', '# scope of data to retrieve \n# 0 = Just get a list of  customers, '
                               '\n# 1 = Get data for all customers'
                               ' \n# 2 = Get data for just a selected customer, \n# default', '1')
        config.set('settings', 'scope', '1')
        config.set('settings', '# If scope is 2, enter the customers ID and Name below default', '123456')
        config.set('settings', 'CustomerID', '123456')
        config.set('settings', '# Set Debug level 0=off 1=on', '0')
        config.set('settings', 'debug', '0')
        config.set('settings', '# Set Token URL default', 'https://id.cisco.com/oauth2/default/v1/token')
        config.set('settings', 'tokenUrl', 'https://id.cisco.com/oauth2/default/v1/token')
        config.set('settings', '# Set Base URL default', 'https://apix.cisco.com/cs/api/v1/')
        config.set('settings', 'baseUrl', 'https://apix.cisco.com/cs/api/v1/')
        config.set('settings', '# Set how many time to loop through script default', '1')
        config.set('settings', 'testLoop', '1')
        config.set('settings', '# Set how many second to wait for the API to respond default', '10')
        config.set('settings', 'urlTimeout', '10')

        with open(configFile, 'w') as configfile:
            config.write(configfile)
        input("Press Enter to continue...")
        sys.exit()

# Function to retrieve raw data from endpoint
def save_json_reply(items, json_filename):
    with open(json_filename, 'w') as json_file:
        json.dump(items, json_file)
    logger(DEBUG, f'Saving {json_file.name}')

# Function to retrieve raw data from endpoint
def get_json_reply(url, tag):
    tries = 1
    response = []

    now = datetime.now()
    logger(DEBUG, f"Start DateTime: {now}")
    logger(DEBUG, f"URL Request:{url}")
    logger(DEBUG, f"{url}")

    while True:
        time.sleep(1/calls_per_sec)
        cdm.token_refresh()
        header = cdm.api_header()

        status_code, response = cdm.api_request("GET", url, header)
        if status_code == 200:
            reply = json.loads(response.text)
            items = reply.get(tag, [])

            logger(DEBUG, f"\nSuccess on Try {tries}!")
            return items

        elif status_code == 400:
            if tries == 1:
                logger(DEBUG, f"400:Retrying ", end="")
                tries += 1
                time.sleep(1)
                continue
            logger(DEBUG, f"400:Aborting ", end="")
            break
        elif status_code == 403: 
            if tries == 1:
                logger(DEBUG, f"403:Retrying", end="")
                tries += 1
                time.sleep(1)
                continue
            logger(DEBUG, f"403:Aborting ", end="")
            break
        
        # Handle some other error cases
        if response:
            logger(DEBUG, f"Status code {status_code}..Continuing.")
            logger(DEBUG, f'Response Body:{response.content}')
                
            logger(DEBUG, f'HTTP Code:{response.status_code}')
            logger(DEBUG, f'Review API Headers:{response.headers}')
            logger(DEBUG, f'Response Body:{response.content}')

            if response.headers.get('X-Mashery-Error-Code') == 'ERR_403_DEVELOPER_OVER_RATE':
                logger(DEBUG, "Over Rate... Sleep one minute and retry")
                logger(WARNING,"Over Rate... Sleep one minute and retry")
                logger(WARNING,"\nResponse Body:", response.content)
                time.sleep(60)

            else:
                error_code = response.content.get('reason', {}).get('errorCode')
                error_info = response.content.get('reason', {}).get('errorInfo')

                if error_code == 'API_INV_000':
                    logger(INFO, f"{error_info}")
                    logger(WARNING,f"{error_info}....Skipping")
                elif error_code == 'API_PARTY_002':
                    logger(INFO, f"{error_info}")
                    logger(WARNING,f"{error_info}....Skipping")
                elif error_code == 'API_EF_0032"':
                    logger(INFO, f"{error_info}")
                    logger(WARNING,f"{error_info}....Skipping")
                break

        else:
            logger(INFO, f"No Response received:{status_code} ... retry {tries}.")
            logger(ERROR, f"No Response received:{status_code} ... retry {tries}.")
            
        tries += 1
        time.sleep(1)
    # end while

    logger(DEBUG, f"Failed to get JSON reply after {tries} tries!")
    return None


# Function to retrieve a list of customers
def get_customers():
    customers = []
    customerHeader = ['customerId', 'customerName', 'streetAddress1', 'streetAddress2', 'streetAddress3',
                      'streetAddress4',
                      'city', 'state', 'country', 'zipCode', 'theaterCode']
    logger(INFO, "Retrieving Customer List....", end="")

    url = f'{baseUrl}customer-info/customer-details'
    items = get_json_reply(url, 'data')
    for x in items:
        listing = [x['customerId'], x['customerName'], x['streetAddress1'], x['streetAddress2'],
                   x['streetAddress3'], x['streetAddress4'], x['city'], x['state'], x['country'], x['zipCode'],
                   x['theaterCode']]
        logger(DEBUG, f'Found customer {listing[1]}')
        customers.append(listing)
    with open('Customers.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(customerHeader)
        writer.writerows(customers)
    logger(INFO, 'Done')


# Function to retrieve a list of contracts
def get_contract_details(customerid, customername):
    contracts = []
    contractsHeader = ['customerId', 'customerName', 'contractNumber', 'contractStatus', 'contractStartDate',
                       'contractEndDate', 'serviceProgram', 'serviceLevel', 'billtoSiteId', 'billtoSiteName',
                       'billtoAddressLine1', 'billtoAddressLine2', 'billtoAddressLine3', 'billtoAddressLine4',
                       'billtoCity', 'billtoState', 'billtoPostalCode', 'billtoProvince', 'billtoCountry',
                       'billtoGuName', 'siteUseName', 'siteUseId', 'siteAddress1', 'siteCity', 'siteStateProvince',
                       'sitePostalCode', 'siteCountry', 'baseProductId']
    csv_filename = csv_output_dir + customerid + '_Contracts_Details.csv'
    json_filename = json_output_dir + customerid + '_Contracts_Details.json'

    logger(INFO, "           Contract Details List....", end="")

    url = f'{baseUrl}contracts/contract-details?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['contractNumber'], x['contractStatus'], x['contractStartDate'],
                       x['contractEndDate'], x['serviceProgram'], x['serviceLevel'], x['billtoSiteId'],
                       x['billtoSiteName'], x['billtoAddressLine1'], x['billtoAddressLine2'], x['billtoAddressLine3'],
                       x['billtoAddressLine4'], x['billtoCity'], x['billtoState'], x['billtoPostalCode'],
                       x['billtoProvince'], x['billtoCountry'], x['billtoGuName'], x['siteUseName'],
                       x['siteUseId'], x['siteAddress1'], x['siteCity'], x['siteStateProvince'],
                       x['sitePostalCode'], x['siteCountry'], x['baseProductId']]
            contracts.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(contractsHeader)
            writer.writerows(contracts)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')

    else:
        logger(INFO, f'Not Available')

# Function to retrieve a list of devices covered
def get_covered(customerid, customername):
    covered = []
    coveredHeader = ['customerid', 'customername', 'serialNumber', 'productId', 'productFamily', 'coverageStatus',
                     'contractInstanceNumber', 'parentContractInstanceId', 'orderShipDate', 'serviceable',
                     'coverageStartDate', 'coverageEndDate', 'warrantyStartDate', 'warrantyEndDate', 'warrantyType',
                     'contractNumber', 'serviceLevel', 'slaType', 'serviceProgram', 'contractStartDate',
                     'contractEndDate', 'contractStatus', 'shiptoSiteId', 'shiptoSiteName', 'shiptoAddressLine1',
                     'shiptoAddressLine2', 'shiptoAddressLine3', 'shiptoAddressLine4', 'shiptoCity', 'shiptoState',
                     'shiptoPostalCode', 'shiptoProvince', 'shiptoCountry', 'installedatSiteId',
                     'installedatSiteName', 'installedatAddressLine1', 'installedatAddressLine2',
                     'installedatAddressLine3', 'installedatAddressLine4', 'installedatCity', 'installedatState',
                     'installedatPostalCode', 'installedatProvince', 'installedatCountry', 'billtoSiteId',
                     'billtoSiteName', 'billtoAddressLine1', 'billtoAddressLine2', 'billtoAddressLine3',
                     'billtoAddressLine4', 'billtoCity', 'billtoState', 'billtoPostalCode', 'billtoProvince',
                     'billtoCountry', 'neInstanceId', 'billtoPartyId', 'installAtGuPartyId', 'contractInstanceId',
                     'serviceLineId', 'serviceLineStatus', 'lineCustomerName', 'businessProcessName', 'entitledParty',
                     'installGUName']
    csv_filename = csv_output_dir + customerid + 'Covered_Assets.csv'
    json_filename = json_output_dir + customerid + 'Covered_Assets.json'

    logger(INFO, "           Covered List....", end="")

    url = f'{baseUrl}contracts/coverage?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['serialNumber'],
                       x['productId'].replace(',', ' '), x['productFamily'].replace(',', ' '), x['coverageStatus'],
                       x['contractInstanceNumber'],
                       x['parentContractInstanceId'], x['orderShipDate'], x['serviceable'], x['coverageStartDate'],
                       x['coverageEndDate'], x['warrantyStartDate'], x['warrantyEndDate'], x['warrantyType'],
                       x['contractNumber'], x['serviceLevel'], x['slaType'], x['serviceProgram'],
                       x['contractStartDate'], x['contractEndDate'], x['contractStatus'], x['shiptoSiteId'],
                       x['shiptoSiteName'], x['shiptoAddressLine1'], x['shiptoAddressLine2'], x['shiptoAddressLine3'],
                       x['shiptoAddressLine4'], x['shiptoCity'], x['shiptoState'], x['shiptoPostalCode'],
                       x['shiptoProvince'], x['shiptoCountry'], x['installedatSiteId'], x['installedatSiteName'],
                       x['installedatAddressLine1'], x['installedatAddressLine2'], x['installedatAddressLine3'],
                       x['installedatAddressLine4'], x['installedatCity'], x['installedatState'],
                       x['installedatPostalCode'], x['installedatProvince'], x['installedatCountry'], x['billtoSiteId'],
                       x['billtoSiteName'], x['billtoAddressLine1'], x['billtoAddressLine2'], x['billtoAddressLine3'],
                       x['billtoAddressLine4'], x['billtoCity'], x['billtoState'], x['billtoPostalCode'],
                       x['billtoProvince'], x['billtoCountry'], x['neInstanceId'], x['billtoPartyId'],
                       x['installAtGuPartyId'], x['contractInstanceId'], x['serviceLineId'], x['serviceLineStatus'],
                       x['lineCustomerName'], x['businessProcessName'], x['entitledParty'], x['installGUName']]
            covered.append(listing)
        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(coveredHeader)
            writer.writerows(covered)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of devices that are not covered under a contract
def get_not_covered(customerid, customername):
    notcovered = []
    notcoveredHeader = ['customerid', 'customername', 'contractInstanceNumber', 'serialNumber', 'productId',
                        'hwType', 'orderShipDate', 'installedatSiteId', 'installedatSiteName',
                        'installedatAddressLine1', 'installedatAddressLine2', 'installedatAddressLine3',
                        'installedatAddressLine4', 'installedatCity', 'installedatState', 'installedatPostalCode',
                        'installedatProvince', 'installedatCountry', 'warrantyType', 'warrantyStartDate',
                        'warrantyEndDate', 'neInstanceId', 'billtoPartyId']
    csv_filename = csv_output_dir + customerid + 'Not_Covered_Assets.csv'
    json_filename = json_output_dir + customerid + 'Not_Covered_Assets.json'

    logger(INFO, "           Not Covered List....", end="")

    url = f'{baseUrl}contracts/not-covered?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['contractInstanceNumber'], x['serialNumber'], x['productId'],
                       x['hwType'], x['orderShipDate'], x['installedatSiteId'], x['installedatSiteName'],
                       x['installedatAddressLine1'], x['installedatAddressLine2'], x['installedatAddressLine3'],
                       x['installedatAddressLine4'], x['installedatCity'], x['installedatState'],
                       x['installedatPostalCode'], x['installedatProvince'], x['installedatCountry'], x['warrantyType'],
                       x['warrantyStartDate'], x['warrantyEndDate'], x['neInstanceId'], x['billtoPartyId']]
            notcovered.append(listing)
        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(notcoveredHeader)
            writer.writerows(notcovered)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of network elements
def get_network_elements(customerid, customername):
    networkElements = []
    networkElementsHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                             'managementAddress', 'neSubtype', 'inventoryAvailability', 'lastConfigRegister',
                             'ipAddress', 'hostname', 'sysName', 'featureSet', 'inventoryCollectionDate',
                             'productFamily', 'productId', 'productType', 'createDate', 'swType', 'swVersion',
                             'reachabilityStatus', 'neType', 'lastReset', 'resetReason', 'sysContact', 'sysDescr',
                             'sysLocation', 'sysObjectId', 'configRegister', 'configAvailability',
                             'configCollectionDate', 'imageName', 'bootstrapVersion', 'isManagedNe', 'userField1',
                             'userField2', 'userField3', 'userField4', 'macAddress']
    csv_filename = csv_output_dir + customerid + '_Assets.csv'
    json_filename = json_output_dir + customerid + '_Assets.json'

    logger(INFO, "           Network Elements List....", end="")

    url = f'{baseUrl}inventory/network-elements?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['inventoryName'],
                       x['managementAddress'], x['neSubtype'], x['inventoryAvailability'], x['lastConfigRegister'],
                       x['ipAddress'], x['hostname'], x['sysName'], x['featureSet'], x['inventoryCollectionDate'],
                       x['productFamily'], x['productId'], x['productType'], x['createDate'], x['swType'],
                       x['swVersion'], x['reachabilityStatus'], x['neType'], x['lastReset'], x['resetReason'],
                       x['sysContact'], x['sysDescr'], x['sysLocation'], x['sysObjectId'], x['configRegister'],
                       x['configAvailability'], x['configCollectionDate'], x['imageName'], x['bootstrapVersion'],
                       x['isManagedNe'], x['userField1'], x['userField2'], x['userField3'], x['userField4'],
                       x['macAddress']]
            networkElements.append(listing)
        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(networkElementsHeader)
            writer.writerows(networkElements)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of inventory groups
def get_inventory_groups(customerid, customername):
    inventory = []
    inventoryHeader = ['customerId', 'customerName', 'inventoryId', 'inventoryName']
    csv_filename = csv_output_dir + customerid + '_Asset_Groups.csv'
    json_filename = json_output_dir + customerid + '_Asset_Groups.json'
    
    logger(INFO, "           Inventory Groups List....", end="")

    url = f'{baseUrl}customer-info/inventory-groups?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['inventoryId'], x['inventoryName']]
            inventory.append(listing)
        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(inventoryHeader)
            writer.writerows(inventory)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of hardware
def get_hardware(customerid, customername):
    hardware = []
    hardwareHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                      'hwInstanceId', 'hwName', 'hwType', 'productSubtype', 'slot', 'productFamily', 'productId',
                      'productType', 'swVersion', 'serialNumber', 'serialNumberStatus', 'hwRevision', 'tan',
                      'tanRevision', 'pcbNumber', 'installedMemory', 'installedFlash', 'collectedSerialNumber',
                      'collectedProductId', 'productName', 'dimensionsFormat', 'dimensions', 'weight',
                      'formFactor', 'supportPage', 'visioStencilUrl', 'smallImageUrl', 'largeImageUrl',
                      'baseProductId', 'productReleaseDate', 'productDescription']
    csv_filename = csv_output_dir + customerid + '_Hardware.csv'
    json_filename = json_output_dir + customerid + '_Hardware.json'

    logger(INFO, "           Hardware List....", end="")

    url = f'{baseUrl}inventory/hardware?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['inventoryName'],
                       x['hwInstanceId'], x['hwName'], x['hwType'], x['productSubtype'], x['slot'], x['productFamily'],
                       x['productId'], x['productType'], x['swVersion'], x['serialNumber'], x['serialNumberStatus'],
                       x['hwRevision'], x['tan'], x['tanRevision'], x['pcbNumber'], x['installedMemory'],
                       x['installedFlash'], x['collectedSerialNumber'], x['collectedProductId'], x['productName'],
                       x['dimensionsFormat'], x['dimensions'], x['weight'], x['formFactor'], x['supportPage'],
                       x['visioStencilUrl'], x['smallImageUrl'], x['largeImageUrl'], x['baseProductId'],
                       x['productReleaseDate'], x['productDescription']]
            hardware.append(listing)
        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareHeader)
            writer.writerows(hardware)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of hardware EOL data
def get_hardware_eol(customerid, customername):
    hardwareEOL = []
    hardwareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwType',
                         'currentHwEolMilestone', 'nextHwEolMilestone', 'hwInstanceId', 'productId',
                         'currentHwEolMilestoneDate', 'nextHwEolMilestoneDate', 'hwEolInstanceId']
    csv_filename = csv_output_dir + customerid + '_Hardware_EOL.csv'
    json_filename = json_output_dir + customerid + '_Hardware_EOL.json'

    logger(INFO, "           Hardware EOL List....", end="")
    url = f'{baseUrl}product-alerts/hardware-eol?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwType'],
                       x['currentHwEolMilestone'], x['nextHwEolMilestone'], x['hwInstanceId'], x['productId'],
                       x['currentHwEolMilestoneDate'], x['nextHwEolMilestoneDate'], x['hwEolInstanceId']]
            hardwareEOL.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLHeader)
            writer.writerows(hardwareEOL)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of hardware EOL bulletins
def get_hardware_eol_bulletins(customerid, customername):
    hardwareEOLBulletins = []
    hardwareEOLBulletinsHeader = ['customerid', 'customername', 'hwEolInstanceId', 'bulletinProductId',
                                  'bulletinNumber', 'bulletinTitle', 'eoLifeAnnouncementDate', 'eoSaleDate',
                                  'lastShipDate', 'eoSwMaintenanceReleasesDate', 'eoRoutineFailureAnalysisDate',
                                  'eoNewServiceAttachmentDate', 'eoServiceContractRenewalDate', 'lastDateOfSupport',
                                  'eoVulnerabilitySecuritySupport', 'url']
    csv_filename = csv_output_dir + customerid + '_Hardware_Bulletins.csv'
    json_filename = json_output_dir + customerid + '_Hardware_Bulletins.json'

    logger(INFO, "           Hardware EOL Bulletins List....", end="")
    url = f'{baseUrl}product-alerts/hardware-eol-bulletins?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['hwEolInstanceId'], x['bulletinProductId'], x['bulletinNumber'],
                       x['bulletinTitle'], x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['lastShipDate'],
                       x['eoSwMaintenanceReleasesDate'], x['eoRoutineFailureAnalysisDate'],
                       x['eoNewServiceAttachmentDate'], x['eoServiceContractRenewalDate'], x['lastDateOfSupport'],
                       x['eoVulnerabilitySecuritySupport'], x['url']]
            hardwareEOLBulletins.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLBulletinsHeader)
            writer.writerows(hardwareEOLBulletins)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of software
def get_software(customerid, customername):
    software = []
    softwareHeader = ['customerid', 'customername', 'managedNeInstanceId', 'inventoryName', 'swType', 'swVersion',
                      'swMajorVersion', 'swCategory', 'swStatus', 'swName']
    csv_filename = csv_output_dir + customerid + '_Software.csv'
    json_filename = json_output_dir + customerid + '_Software.json'

    logger(INFO, "           Software List....", end="")
    url = f'{baseUrl}inventory/software?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['managedNeInstanceId'], x['inventoryName'], x['swType'],
                       x['swVersion'], x['swMajorVersion'], x['swCategory'], x['swStatus'], x['swName']]
            software.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softwareHeader)
            writer.writerows(software)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of software EOL data
def get_software_eol(customerid, customername):
    softewareEOL = []
    softewareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'swType', 'currentSwEolMilestone', 'nextSwEolMilestone', 'swVersion',
                          'currentSwEolMilestoneDate', 'nextSwEolMilestoneDate', 'swEolInstanceId']
    csv_filename = csv_output_dir + customerid + '_Software_EOL.csv'
    json_filename = json_output_dir + customerid + '_Software_EOL.json'
    
    logger(INFO, "           Software EOL List....", end="")

    url = f'{baseUrl}product-alerts/software-eol?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'],
                       x['swType'], x['currentSwEolMilestone'], x['nextSwEolMilestone'], x['swVersion'],
                       x['currentSwEolMilestoneDate'], x['nextSwEolMilestoneDate'], x['swEolInstanceId']]
            softewareEOL.append(listing)


        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLHeader)
            writer.writerows(softewareEOL)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of software EOL bulletins
def get_software_eol_bulletins(customerid, customername):
    softewareEOLBulletins = []
    softewareEOLBulletinsHeader = ['customerid', 'customername', 'swEolInstanceId', 'bulletinNumber',
                                   'bulletinTitle', 'swMajorVersion', 'swMaintenanceVersion', 'swTrain', 'swType',
                                   'eoLifeAnnouncementDate', 'eoSaleDate', 'eoSwMaintenanceReleasesDate',
                                   'eoVulnerabilitySecuritySupport', 'lastDateOfSupport', 'url']
    csv_filename = csv_output_dir + customerid + '_Software_Bulletins.csv'
    json_filename = json_output_dir + customerid + '_Software_Bulletins.json'

    logger(INFO, "           Software EOL Bulletins List....", end="")

    url = f'{baseUrl}product-alerts/software-eol-bulletins?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['swEolInstanceId'], x['bulletinNumber'], x['bulletinTitle'],
                       x['swMajorVersion'], x['swMaintenanceVersion'], x['swTrain'], x['swType'],
                       x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['eoSwMaintenanceReleasesDate'],
                       x['eoVulnerabilitySecuritySupport'], x['lastDateOfSupport'], x['url']]
            softewareEOLBulletins.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLBulletinsHeader)
            writer.writerows(softewareEOLBulletins)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of field notices
def get_fieldnotices(customerid, customername):
    fieldNotices = []
    fieldNoticesHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'vulnerabilityStatus', 'vulnerabilityReason', 'hwInstanceId', 'bulletinNumber']
    csv_filename = csv_output_dir + customerid + '_Field_Notices.csv'
    json_filename = json_output_dir + customerid + '_Field_Notices.json'
    
    logger(INFO, "           Field Notices List....", end="")

    url = f'{baseUrl}product-alerts/field-notices?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['vulnerabilityStatus'],
                       x['vulnerabilityReason'], x['hwInstanceId'], x['bulletinNumber']]
            fieldNotices.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticesHeader)
            writer.writerows(fieldNotices)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of field notice bulletins
def get_fieldnoticebulletins(customerid, customername):
    fieldNoticeBulletins = []
    fieldNoticeBulletinsHeader = ['customerid', 'customername', 'bulletinFirstPublished', 'bulletinNumber',
                                  'fieldNoticeType', 'bulletinTitle', 'bulletinLastUpdated',
                                  'alertAutomationCaveat', 'url', 'bulletinSummary']
    csv_filename = csv_output_dir + customerid + '_Feild_Notice_Bulletins.csv'
    json_filename = json_output_dir + customerid + '_Feild_Notice_Bulletins.json'

    logger(INFO, "           Field Notice Bulletins List....", end="")

    url = f'{baseUrl}product-alerts/field-notice-bulletins?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['bulletinFirstPublished'], x['bulletinNumber'], x['fieldNoticeType'],
                       x['bulletinTitle'], x['bulletinLastUpdated'], x['alertAutomationCaveat'], x['url'],
                       x['bulletinSummary']]
            fieldNoticeBulletins.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticeBulletinsHeader)
            writer.writerows(fieldNoticeBulletins)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of security advisories
def get_security_advisory(customerid, customername):
    securityAdvisory = []
    securityAdvisoryHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwInstanceId',
                              'vulnerabilityStatus', 'vulnerabilityReason', 'securityAdvisoryInstanceId']
    csv_filename = csv_output_dir + customerid + '_Security_Advisories.csv'
    json_filename = json_output_dir + customerid + '_Security_Advisories.json'

    logger(INFO, "           Security Advisory List....", end="")

    url = f'{baseUrl}product-alerts/security-advisories?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwInstanceId'],
                       x['vulnerabilityStatus'], x['vulnerabilityReason'], x['securityAdvisoryInstanceId']]
            securityAdvisory.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryHeader)
            writer.writerows(securityAdvisory)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')

# Function to retrieve a list of security advisory bulletins
def get_security_advisory_bulletins(customerid, customername):
    securityAdvisoryBulletins = []
    securityAdvisoryBulletinsHeader = ['customerid', 'customername', 'securityAdvisoryInstanceId', 'url',
                                       'bulletinVersion', 'advisoryId', 'bulletinTitle', 'bulletinFirstPublished',
                                       'bulletinLastUpdated', 'securityImpactRating', 'bulletinSummary',
                                       'alertAutomationCaveat', 'cveId', 'cvssBaseScore', 'cvssTemporalScore',
                                       'ciscoBugIds']
    csv_filename = csv_output_dir + customerid + '_Security_Advisory_Bulletins.csv'
    json_filename = json_output_dir + customerid + '_Security_Advisory_Bulletins.json'

    logger(INFO, "           Security Advisory Bulletins List....", end="")

    url = f'{baseUrl}product-alerts/security-advisory-bulletins?customerId={customerid}'
    items = get_json_reply(url, 'data')
    if items:
        for x in items:
            listing = [customerid, customername, x['securityAdvisoryInstanceId'], x['url'], x['bulletinVersion'],
                       x['advisoryId'], x['bulletinTitle'], x['bulletinFirstPublished'], x['bulletinLastUpdated'],
                       x['securityImpactRating'], x['bulletinSummary'], x['alertAutomationCaveat'], x['cveId'],
                       x['cvssBaseScore'], x['cvssTemporalScore'], x['ciscoBugIds']]
            securityAdvisoryBulletins.append(listing)

        with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryBulletinsHeader)
            writer.writerows(securityAdvisoryBulletins)

        # save the JSON response if requested
        save_json_reply(items, json_filename)
        logger(INFO, 'Done')
    else:
        logger(INFO, f'Not Available')


# Function to retrieve a list of customers
def get_customer_data():
    logger(INFO, "Retrieving Customers Data....")
    if scope == 0:
        logger(DEBUG, f'Script Completed successfully')
        exit()
    else:
        with open('Customers.csv', 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']
                if scope == 1:
                    get_all_data(str(customerId), customer)
                elif scope == 2:
                    if int(customerId) == customerID:
                        get_all_data(str(customerId), customer)
                #if
            # for
        # with
    #else

def delete_empty_folder(folder):
    deleted_folder = False
    # Check if the directory contains any files
    if not os.listdir(folder):
        # Remove the directory if it has no files
        shutil.rmtree(folder)
        deleted_folder = True
    # end if

    return deleted_folder
    
# Function to retrieve data for all customers
def get_all_data(customerid, customer):
    logger(INFO, f'  Scanning {customer} :: {customerid}')

    current_dir = os.getcwd()

    # Create the customers directory (if needed) and change to it
    os.makedirs(customer, exist_ok=True)

    # create output directories
    os.chdir(customer)
    cdm.storage(csv_output_dir, json_output_dir, None)
    
    get_contract_details(customerid, customer)
    get_covered(customerid, customer)
    get_not_covered(customerid, customer)
    get_network_elements(customerid, customer)
    get_inventory_groups(customerid, customer)
    get_hardware(customerid, customer)
    get_hardware_eol(customerid, customer)
    get_hardware_eol_bulletins(customerid, customer)
    get_software(customerid, customer)
    get_software_eol(customerid, customer)
    get_software_eol_bulletins(customerid, customer)
    get_fieldnotices(customerid, customer)
    get_fieldnoticebulletins(customerid, customer)
    get_security_advisory(customerid, customer)
    get_security_advisory_bulletins(customerid, customer)

    # Check if the directory contains any files
    delete_empty_folder(csv_output_dir)
    delete_empty_folder(json_output_dir)
    
    # back to the partner directory
    os.chdir(current_dir)
    if delete_empty_folder(customer):
        logger(INFO, f"    No Report Data: Deleting {customer}")
    else:
        logger(INFO, f"    All Reports complete")

    
'''
Begin main application control
=======================================================================
'''
if __name__ == '__main__':
    count = 0

    # setup parser
    parser = argparse.ArgumentParser(description="Your script description.")
    parser.add_argument("partner", nargs='?', default='credentials', help="Partner name")
    parser.add_argument("-log", "--log-level", default="INFO", help="Set the logging level (default: INFO)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print log message to console")

    # Parse command-line arguments
    args = parser.parse_args()
    partner = args.partner
    verbose = args.verbose

    # call function to load config.ini data into variables
    load_config(partner)

    # create a per-partner folder for saving data
    if partner:
        if os.path.isdir(partner):
            shutil.rmtree(partner)
        # Create the partners directory
        os.makedirs(partner, exist_ok=True)
        # Change into the directory
        os.chdir(partner)

    # setup the logging level
    cdm.storage(None, None, log_output_dir)
    init_logger(args.log_level.upper(), verbose)

    logger(INFO, f'\nScript is executing {testLoop} Time(s)')
    for count in range(0, testLoop):
        logger(INFO, f'Execution:{count + 1} of {testLoop}')
        cdm.token_get()
        get_customers()
        get_customer_data()

        logger(DEBUG, f'Script Completed {count + 1} time(s) successfully')
        logger(INFO, f'Script Completed {count + 1} time(s) successfully')
        if count + 1 == testLoop:
            # Clean exit
            exit()
        else:
            # pause 5 sec between each itteration
            logger(INFO, '\n\npausing for 2 secs')
            logger(DEBUG, '=================================================================')
            time.sleep(2)
    # end for
# end
