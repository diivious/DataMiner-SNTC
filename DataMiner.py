#
#
# adding Cisco DataMiner Module system path
import sys
sys.path.insert(0, '../cdm')

# import library to use HTTP and JSON request
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
csv_output_dir = "outputcsv/"
log_output_dir = "outputlog/"
log_output_dir = "outputlog/"
temp_dir = "temp/"
outputFormat = 3 	   # 1=both, 2=json, 3=CSV

# Debug Variables
scope = '1'
customerID = 0
debug = 0
fmt = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
testLoop = 0
logfile = 'SNTC_DataMiner_log.txt'

'''
Begin defining functions
=======================================================================
'''
def init_logger(log_level):
    # Check if the specified log level is valid
    #   CRITICAL: Indicates a very serious error, typically leading to program termination.
    #   ERROR:    Indicates an error that caused the program to fail to perform a specific function.
    #   WARNING:  Indicates a warning that something unexpected happened
    #   INFO:     Provides confirmation that things are working as expected
    #   DEBUG:    Provides info useful for diagnosing problems
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        print("Invalid log level. Please use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        exit(1)

    # Setup log storage - incase needed
    if os.path.isdir(log_output_dir):
        shutil.rmtree(log_output_dir)
    os.mkdir(log_output_dir)

    # Set up logging based on the parsed log level
    logging.basicConfig(filename=log_output_dir + 'SNTC.log', level=log_level,
                        format='%(levelname)s:%(funcName)s: %(message)s')
    logger = logging.getLogger(__name__)
    return logger

# Function explain usage
def usage():
    print(f"Usage: python3 {sys.argv[0]} <customer> -log=<LOG_LEVEL>")
    print(f"Args:")
    print(f"   Optional named section for customer auth credentials.\n")
    sys.exit()

# Function to load configuration from config.ini and continue or create a template if not found and exit
def load_config(customer):
    global scope
    global customerID
    global debug
    global baseUrl
    global testLoop

    if os.path.isfile(logfile):
        os.remove(logfile)

    config = ConfigParser()
    if os.path.isfile(configFile):
        print('Config.ini file was found, continuing...')
        config.read(configFile)

        # check to see if credentials exist for a named customer.
        # default customer config is 'credentials'
        if not customer in config:
            print(f"\nError: Credentials for Customer {customer} not found in config.ini")
            usage()

        # [credentials]
        cdm.clientId = (config[customer]['clientId'])
        cdm.clientSecret = (config[customer]['clientSecret'])

        # [Settings]
        cdm.tokenUrl = (config['settings']['tokenUrl'])
        cdm.urlTimeout = int((config['settings']['urlTimeout']))

        customerID = int((config['settings']['customerID']))
        debug = int((config['settings']['debug']))
        testLoop = int((config['settings']['testLoop']))
        scope = int((config['settings']['scope']))
        baseUrl = (config['settings']['baseUrl'])
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
        exit()

# Function to retrieve raw data from endpoint
def get_json_reply(url, tag):
    tries = 1
    response = []

    now = datetime.now()
    logging.debug(f"Start DateTime: {now}")
    logging.debug(f"URL Request:{url}")

    logging.debug(f"{url}")
    while True:
        time.sleep(1/calls_per_sec)
        cdm.token_refresh()
        header = cdm.api_header()

        status_code, response = cdm.api_request("GET", url, header)
        if status_code == 200:
            reply = json.loads(response.text)
            items = reply.get(tag, [])

            logging.debug("\nSuccess on Try {tries}! \nContinuing.")
            if tries > 1: print(f"\nSuccess on Try {tries}! \nContinuing.")
            return items

        elif status_code == 403:
            break
        
        # Handle some other error cases
        if response:
            print(f"Status code {status_code}..Continuing.")
            print(f'Response Body:{response.content}')
                
            logging.debug(f'HTTP Code:{response.status_code}')
            logging.debug(f'Review API Headers:{response.headers}')
            logging.debug(f'Response Body:{response.content}')

            if response.headers.get('X-Mashery-Error-Code') == 'ERR_403_DEVELOPER_OVER_RATE':
                print("Over Rate... Sleep one minute and retry")
                logging.warning("Over Rate... Sleep one minute and retry")
                logging.warning("\nResponse Body:", response.content)
                time.sleep(60)

            else:
                error_code = response.content.get('reason', {}).get('errorCode')
                error_info = response.content.get('reason', {}).get('errorInfo')

                if error_code == 'API_INV_000':
                    print(f"{error_info}")
                    logging.warning(f"{error_info}....Skipping")
                elif error_code == 'API_PARTY_002':
                    print(f"{error_info}")
                    logging.warning(f"{error_info}....Skipping")
                break

        else:
            print(f"No Response received:  {status_code} ... retry {tries}.")
            logging.error(f"No Response received:{status_code} ... retry {tries}.")
            
        if tries > 1: logging.info(f"Get Reply - retry {tries}.")
        tries += 1
        time.sleep(1)
    # end while

    logging.error(f"Failed to get JSON reply after {tries} tries!")
    return None


# Function to retrieve a list of customers
def get_customers():
    customers = []
    customerHeader = ['customerId', 'customerName', 'streetAddress1', 'streetAddress2', 'streetAddress3',
                      'streetAddress4',
                      'city', 'state', 'country', 'zipCode', 'theaterCode']
    print("Retrieving Customer List....", end="")

    url = f'{baseUrl}customer-info/customer-details'
    items = get_json_reply(url, 'data')
    for x in items:
        listing = [x['customerId'], x['customerName'], x['streetAddress1'], x['streetAddress2'],
                   x['streetAddress3'], x['streetAddress4'], x['city'], x['state'], x['country'], x['zipCode'],
                   x['theaterCode']]
        logging.debug(f'Found customer {listing[1]}')
        customers.append(listing)
    with open(csv_output_dir + 'customers.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(customerHeader)
        writer.writerows(customers)
    print('Done!')


# Function to retrieve a list of contracts
def get_contract_details(customerid, customername):
    contracts = []
    contractsHeader = ['customerId', 'customerName', 'contractNumber', 'contractStatus', 'contractStartDate',
                       'contractEndDate', 'serviceProgram', 'serviceLevel', 'billtoSiteId', 'billtoSiteName',
                       'billtoAddressLine1', 'billtoAddressLine2', 'billtoAddressLine3', 'billtoAddressLine4',
                       'billtoCity', 'billtoState', 'billtoPostalCode', 'billtoProvince', 'billtoCountry',
                       'billtoGuName', 'siteUseName', 'siteUseId', 'siteAddress1', 'siteCity', 'siteStateProvince',
                       'sitePostalCode', 'siteCountry', 'baseProductId']
    csv_filename = csv_output_dir + customerid + 'Contracts_Details.csv'

    print("           Contract Details List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')

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

    print("           Covered List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


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

    print("           Not Covered List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


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
    csv_filename = csv_output_dir + customerid + 'Assets.csv'

    print("           Network Elements List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of inventory groups
def get_inventory_groups(customerid, customername):
    inventory = []
    inventoryHeader = ['customerId', 'customerName', 'inventoryId', 'inventoryName']
    csv_filename = csv_output_dir + customerid + 'Asset_Groups.csv'
    
    print("           Inventory Groups List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


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

    print("           Hardware List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of hardware EOL data
def get_hardware_eol(customerid, customername):
    hardwareEOL = []
    hardwareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwType',
                         'currentHwEolMilestone', 'nextHwEolMilestone', 'hwInstanceId', 'productId',
                         'currentHwEolMilestoneDate', 'nextHwEolMilestoneDate', 'hwEolInstanceId']
    csv_filename = csv_output_dir + customerid + '_Hardware_EOL.csv'

    print("           Hardware EOL List....", end="")
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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of hardware EOL bulletins
def get_hardware_eol_bulletins(customerid, customername):
    hardwareEOLBulletins = []
    hardwareEOLBulletinsHeader = ['customerid', 'customername', 'hwEolInstanceId', 'bulletinProductId',
                                  'bulletinNumber', 'bulletinTitle', 'eoLifeAnnouncementDate', 'eoSaleDate',
                                  'lastShipDate', 'eoSwMaintenanceReleasesDate', 'eoRoutineFailureAnalysisDate',
                                  'eoNewServiceAttachmentDate', 'eoServiceContractRenewalDate', 'lastDateOfSupport',
                                  'eoVulnerabilitySecuritySupport', 'url']
    csv_filename = csv_output_dir + customerid + '_Hardware_Bulletins.csv'

    print("           Hardware EOL Bulletins List....", end="")
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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of software
def get_software(customerid, customername):
    software = []
    softwareHeader = ['customerid', 'customername', 'managedNeInstanceId', 'inventoryName', 'swType', 'swVersion',
                      'swMajorVersion', 'swCategory', 'swStatus', 'swName']
    csv_filename = csv_output_dir + customerid + '_Software.csv'

    print("           Software List....", end="")
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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of software EOL data
def get_software_eol(customerid, customername):
    softewareEOL = []
    softewareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'swType', 'currentSwEolMilestone', 'nextSwEolMilestone', 'swVersion',
                          'currentSwEolMilestoneDate', 'nextSwEolMilestoneDate', 'swEolInstanceId']
    csv_filename = csv_output_dir + customerid + '_Software_EOL.csv'
    
    print("           Software EOL List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of software EOL bulletins
def get_software_eol_bulletins(customerid, customername):
    softewareEOLBulletins = []
    softewareEOLBulletinsHeader = ['customerid', 'customername', 'swEolInstanceId', 'bulletinNumber',
                                   'bulletinTitle', 'swMajorVersion', 'swMaintenanceVersion', 'swTrain', 'swType',
                                   'eoLifeAnnouncementDate', 'eoSaleDate', 'eoSwMaintenanceReleasesDate',
                                   'eoVulnerabilitySecuritySupport', 'lastDateOfSupport', 'url']
    csv_filename = csv_output_dir + customerid + '_Software_Bulletins.csv'

    print("           Software EOL Bulletins List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of field notices
def get_fieldnotices(customerid, customername):
    fieldNotices = []
    fieldNoticesHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'vulnerabilityStatus', 'vulnerabilityReason', 'hwInstanceId', 'bulletinNumber']
    csv_filename = csv_output_dir + customerid + '_Field_Notices.csv'
    
    print("           Field Notices List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of field notice bulletins
def get_fieldnoticebulletins(customerid, customername):
    fieldNoticeBulletins = []
    fieldNoticeBulletinsHeader = ['customerid', 'customername', 'bulletinFirstPublished', 'bulletinNumber',
                                  'fieldNoticeType', 'bulletinTitle', 'bulletinLastUpdated',
                                  'alertAutomationCaveat', 'url', 'bulletinSummary']
    csv_filename = csv_output_dir + customerid + '_Feild_Notice_Bulletins.csv'

    print("           Field Notice Bulletins List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')


# Function to retrieve a list of security advisories
def get_security_advisory(customerid, customername):
    securityAdvisory = []
    securityAdvisoryHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwInstanceId',
                              'vulnerabilityStatus', 'vulnerabilityReason', 'securityAdvisoryInstanceId']
    csv_filename = csv_output_dir + customerid + '_Security_Advisories.csv'

    print("           Security Advisory List....", end="")

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
        print('Done')
    else:
        print(f'Not Available')

# Function to retrieve a list of security advisory bulletins
def get_security_advisory_bulletins(customerid, customername):
    securityAdvisoryBulletins = []
    securityAdvisoryBulletinsHeader = ['customerid', 'customername', 'securityAdvisoryInstanceId', 'url',
                                       'bulletinVersion', 'advisoryId', 'bulletinTitle', 'bulletinFirstPublished',
                                       'bulletinLastUpdated', 'securityImpactRating', 'bulletinSummary',
                                       'alertAutomationCaveat', 'cveId', 'cvssBaseScore', 'cvssTemporalScore',
                                       'ciscoBugIds']
    csv_filename = csv_output_dir + customerid + '_Security_Advisory__Bulletins.csv'

    print("           Security Advisory Bulletins List....", end="")

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
        print('Done\n')
    else:
        print(f'Not Available')


# Function to retrieve a list of customers
def get_customer_data():
    print("Retrieving Customers Data....")
    if scope == 0:
        logging.debug(f'Script Completed successfully')
        exit()
    elif scope == 1:
        with open(csv_output_dir + 'Customers.csv', 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']
                get_all_data(customerId, customer)
    elif scope == 2:
        with open(csv_output_dir + 'Customers.csv', 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']
                if int(customerId) == customerID:
                    get_all_data(str(customerId), customer)


# Function to retrieve data for all customers
def get_all_data(customerid, customer):
    print(f'  Scanning {customer}')

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

'''
Begin main application control
=======================================================================
'''
if __name__ == '__main__':
    count = 0

    # setup parser
    parser = argparse.ArgumentParser(description="Your script description.")
    parser.add_argument("customer", nargs='?', default='credentials', help="Customer name")
    parser.add_argument("-log", "--log-level", default="DEBUG", help="Set the logging level (default: CRITICAL)")

    # Parse command-line arguments
    args = parser.parse_args()

    # call function to load config.ini data into variables
    customer = args.customer
    load_config(customer)

    # create a per-customer folder for saving data
    if customer:
        # Create the customers directory
        os.makedirs(customer, exist_ok=True)
        # Change into the directory
        os.chdir(customer)

    # delete temp and output directories and recreate before every run
    json_dir = json_output_dir if outputFormat == 1 or outputFormat == 2 else None
    csv_dir = csv_output_dir if outputFormat == 1 or outputFormat == 3 else None
    cdm.storage(csv_dir, json_dir, temp_dir)

    # setup the logging level
    logger = init_logger(args.log_level.upper())

    print(f'\nScript is executing {testLoop} Time(s)')
    for count in range(0, testLoop):
        print(f'Execution:{count + 1} of {testLoop}')
        cdm.token_get()
        get_customers()
        get_customer_data()

        logging.debug(f'Script Completed {count + 1} time(s) successfully')
        print(f'Script Completed {count + 1} time(s) successfully')
        if count + 1 == testLoop:
            # Clean exit
            exit()
        else:
            # pause 5 sec between each itteration
            print('\n\npausing for 2 secs')
            logging.debug('=================================================================')
            time.sleep(2)
    # end for
# end
