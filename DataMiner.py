#
#
#
# adding Cisco DataMiner Folder to system path
import sys
sys.path.insert(0, '../cdm')


# import library to use HTTP and JSON request
import os
import shutil
import csv
import time
import sys
import math
from configparser import ConfigParser
import random
import logging
import argparse
from configparser import ConfigParser

import cdm
from cdm import tokenUrl
from cdm import grantType
from cdm import clientId
from cdm import clientSecret
from cdm import cacheControl
from cdm import authScope
from cdm import urlTimeout

# Cisco DataMiner Module Variables
# =======================================================================
cdm.tokenUrl = "https://id.cisco.com/oauth2/aus1o4emxorc3wkEe5d7/v1/token"

# SNTC settings
# =======================================================================
# Data Initializer Variables
csv_output_dir = 'outputcsv/'
log_output_dir = "outputlog/"
log_to_file = 0  # send all screen logging to a file (1=True, 0=False) default is 0

scope = '1'
customerID = 0
debug = 0
configFile = 'config.ini'
fmt = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
testloop = 1


# SNTC settings
# =======================================================================
# Generic URL Variables
urlBase = ''
urlProtocol = "https://"
urlHost = "api-cx.cisco.com/"
urlLink = ''
environment = ''

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

    # Set up logging based on the parsed log level
    logging.basicConfig(format='%(levelname)s:%(funcName)s: %(message)s', level=log_level, stream=sys.stdout)
    logger = logging.getLogger(__name__)

    # Create a StreamHandler with flush set to True
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    return logger

def init_debug_file(count):
    if log_to_file == 1:
        print(f"Logging output to file SNTC_##.log for version {codeVersion}")
        sys.stdout = open(log_output_dir + 'SNTC_' + str(count) + '.log', 'wt')
    #end if

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
    global urlBase
    global testloop
    global log_to_file

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
        cdm.tokenUrl = (config['settings']['tokenUrl'])

        scope = int((config['settings']['scope']))
        customerID = int((config['settings']['customerID']))
        debug = int((config['settings']['debug']))
        log_to_file = int(config['settings']["log_to_file"])

        urlBase = (config['settings']['urlBase'])
        testloop = int((config['settings']['testloop']))
        cdm.urlTimeout = int((config['settings']['urlTimeout']))


    else:
        print('Config.ini not found!!!!!!!!!!!!\nCreating config.ini...')
        print('\nNOTE: you must edit the config.ini file with your information\nExiting...')
        config.add_section(customer)
        config.set(customer, 'clientId', 'clientId')
        config.set(customer, 'clientSecret', 'clientSecret')
        config.add_section('settings')
        config.set('settings', '# data to retrieve - default value is 1 \n'
                               '# 0 = Just get a list of  customers, \n' 
                               '# 1 = Get data for all customers \n'
                               '# 2 = Get data for just a selected customer, \n')
        config.set('settings', 'scope', '1')
        config.set('settings', '# If scope is 2, enter the customers ID and Name below default', '123456')
        config.set('settings', 'CustomerID', '123456')
        config.set('settings', '# Set Debug level 0=off 1=on', '0')
        config.set('settings', 'debug', '0')
        config.set("settings", "# send all screen logging to a file (1=True, 0=False), default", "0")
        config.set("settings", "log_to_file", "0")
        config.set('settings', '# Set Token URL default', 'https://id.cisco.com/oauth2/default/v1/token')
        config.set('settings', 'tokenUrl', 'https://id.cisco.com/oauth2/default/v1/token')
        config.set('settings', '# Set Base URL default', 'https://apix.cisco.com/cs/api/v1/')
        config.set('settings', 'urlBase', 'https://apix.cisco.com/cs/api/v1/')
        config.set('settings', '# Set how many time to loop through script default', '1')
        config.set('settings', 'testloop', '1')
        config.set('settings', '# Set how many second to wait for the API to respond default', '10')
        config.set('settings', 'urlTimeout', '10')

        with open(configFile, 'w') as configfile:
            config.write(configfile)
        input("Press Enter to continue...")
        exit()

# Function to retrieve raw data from endpoint
def get_json_reply(url):
    tries = 1
    response = []

    while tries < 3:
        try:
            headers = cdm.api_header()
            response = cdm.api_request("GET", url, headers)
            if response:
                if response.status_code == 200:
                    break
                if response.text.__contains__('Customer Id is not associated with Partner'):
                    logging.error('Customer is not associated with Partner')
                    break
            else:
                # if we did not get a resonse, its a hard failure
                    logging.error('Failed to get response to request')
                    break               
        finally:
            tries += 1
            cdm.token_refresh()
            time.sleep(tries)  # increase the wait with the number of retries

    # end while
    if response and response.status_code == 200:
        reply = response.json()
        if debug == 1:
            logging.debug(reply)
        if tries == 1:
            logging.debug(f'Collection was successful')
        else:
            logging.debug(f'Collection retry # {i + 1} was successful')
        return reply

    else:
        logging.critical('Failed to get Collection')
    return []


# Function to retrieve a list of customers
def get_customers():
    url = f'{urlBase}customer-info/customer-details'
    customers = []
    customerHeader = ['customerId', 'customerName', 'streetAddress1', 'streetAddress2', 'streetAddress3',
                      'streetAddress4',
                      'city', 'state', 'country', 'zipCode', 'theaterCode']

    print("\nRetrieving Customer list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [x['customerId'], x['customerName'], x['streetAddress1'], x['streetAddress2'],
                       x['streetAddress3'], x['streetAddress4'], x['city'], x['state'], x['country'], x['zipCode'],
                       x['theaterCode']]
            logging.debug(f'Found customer {listing[1]}')
            customers.append(listing)

        csv_file = (csv_output_dir + cdm.filename('customers.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(customerHeader)
            writer.writerows(customers)

        print('Customer List Done!')
    else:
        print('Failed to get Customer List!')

    return jsonData != None
        

# Function to retrieve a list of contracts
def get_contract_details(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}contracts/contract-details?customerId={customerid}'
    contracts = []
    contractsHeader = ['customerid', 'customername', 'contractNumber', 'contractStatus', 'contractStartDate',
                       'contractEndDate', 'serviceProgram', 'serviceLevel', 'billtoSiteId', 'billtoSiteName',
                       'billtoAddressLine1', 'billtoAddressLine2', 'billtoAddressLine3', 'billtoAddressLine4',
                       'billtoCity', 'billtoState', 'billtoPostalCode', 'billtoProvince', 'billtoCountry',
                       'billtoGuName', 'siteUseName', 'siteUseId', 'siteAddress1', 'siteCity', 'siteStateProvince',
                       'sitePostalCode', 'siteCountry', 'baseProductId']

    print("\nRetrieving Contract Details....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['contractNumber'], x['contractStatus'], x['contractStartDate'],
                       x['contractEndDate'], x['serviceProgram'], x['serviceLevel'], x['billtoSiteId'],
                       x['billtoSiteName'], x['billtoAddressLine1'], x['billtoAddressLine2'], x['billtoAddressLine3'],
                       x['billtoAddressLine4'], x['billtoCity'], x['billtoState'], x['billtoPostalCode'],
                       x['billtoProvince'], x['billtoCountry'], x['billtoGuName'], x['siteUseName'],
                       x['siteUseId'], x['siteAddress1'], x['siteCity'], x['siteStateProvince'],
                       x['sitePostalCode'], x['siteCountry'], x['baseProductId']]
            contracts.append(listing)

        csv_file = (csv_output_dir + cdm.filename('contracts.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(contractsHeader)
            writer.writerows(contracts)
        print('Contract List Done')
    else:
        print('Failed to get Contract List!')


# Function to retrieve a list of devices covered
def get_covered(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}contracts/coverage?customerId={customerid}'
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

    print("\nRetrieving Covered list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
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

        csv_file = (csv_output_dir + cdm.filename('covered.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(coveredHeader)
            writer.writerows(covered)
        print('Covered List Done')
    else:
        print('Failed to get Covered List!')


# Function to retrieve a list of devices that are not covered under a contract
def get_not_covered(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}contracts/not-covered?customerId={customerid}'
    notcovered = []
    notcoveredHeader = ['customerid', 'customername', 'contractInstanceNumber', 'serialNumber', 'productId',
                        'hwType', 'orderShipDate', 'installedatSiteId', 'installedatSiteName',
                        'installedatAddressLine1', 'installedatAddressLine2', 'installedatAddressLine3',
                        'installedatAddressLine4', 'installedatCity', 'installedatState', 'installedatPostalCode',
                        'installedatProvince', 'installedatCountry', 'warrantyType', 'warrantyStartDate',
                        'warrantyEndDate', 'neInstanceId', 'billtoPartyId']

    print("\nRetrieving Not Covered list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['contractInstanceNumber'], x['serialNumber'], x['productId'],
                       x['hwType'], x['orderShipDate'], x['installedatSiteId'], x['installedatSiteName'],
                       x['installedatAddressLine1'], x['installedatAddressLine2'], x['installedatAddressLine3'],
                       x['installedatAddressLine4'], x['installedatCity'], x['installedatState'],
                       x['installedatPostalCode'], x['installedatProvince'], x['installedatCountry'], x['warrantyType'],
                       x['warrantyStartDate'], x['warrantyEndDate'], x['neInstanceId'], x['billtoPartyId']]
            notcovered.append(listing)

        csv_file = (csv_output_dir + cdm.filename('not_covered.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(notcoveredHeader)
            writer.writerows(notcovered)
        print('Not Covered List Done')
    else:
        print('Failed to get Not Covered List!')


# Function to retrieve a list of network elements
def get_network_elements(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}inventory/network-elements?customerId={customerid}'
    networkElements = []
    networkElementsHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                             'managementAddress', 'neSubtype', 'inventoryAvailability', 'lastConfigRegister',
                             'ipAddress', 'hostname', 'sysName', 'featureSet', 'inventoryCollectionDate',
                             'productFamily', 'productId', 'productType', 'createDate', 'swType', 'swVersion',
                             'reachabilityStatus', 'neType', 'lastReset', 'resetReason', 'sysContact', 'sysDescr',
                             'sysLocation', 'sysObjectId', 'configRegister', 'configAvailability',
                             'configCollectionDate', 'imageName', 'bootstrapVersion', 'isManagedNe', 'userField1',
                             'userField2', 'userField3', 'userField4', 'macAddress']

    print("\nRetrieving Network Elements list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
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

        csv_file = (csv_output_dir + cdm.filename('network_elements.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(networkElementsHeader)
            writer.writerows(networkElements)
        print('Network Elements List Done')
    else:
        print('Failed to get Network Elements List')


# Function to retrieve a list of inventory groups
def get_inventory_groups(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}customer-info/inventory-groups?customerId={customerid}'
    inventory = []
    inventoryHeader = ['customerId', 'customerName', 'inventoryId', 'inventoryName']

    print("\nRetrieving Inventory Groups list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['inventoryId'], x['inventoryName']]
            inventory.append(listing)

        csv_file = (csv_output_dir + cdm.filename('inventory.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(inventoryHeader)
            writer.writerows(inventory)
        print('Inventory List Done')
    else:
        print('Failed to get Inventory List')


# Function to retrieve a list of hardware
def get_hardware(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}inventory/hardware?customerId={customerid}'
    hardware = []
    hardwareHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                      'hwInstanceId', 'hwName', 'hwType', 'productSubtype', 'slot', 'productFamily', 'productId',
                      'productType', 'swVersion', 'serialNumber', 'serialNumberStatus', 'hwRevision', 'tan',
                      'tanRevision', 'pcbNumber', 'installedMemory', 'installedFlash', 'collectedSerialNumber',
                      'collectedProductId', 'productName', 'dimensionsFormat', 'dimensions', 'weight',
                      'formFactor', 'supportPage', 'visioStencilUrl', 'smallImageUrl', 'largeImageUrl',
                      'baseProductId', 'productReleaseDate', 'productDescription']

    print("\nRetrieving Hardware list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['inventoryName'],
                       x['hwInstanceId'], x['hwName'], x['hwType'], x['productSubtype'], x['slot'], x['productFamily'],
                       x['productId'], x['productType'], x['swVersion'], x['serialNumber'], x['serialNumberStatus'],
                       x['hwRevision'], x['tan'], x['tanRevision'], x['pcbNumber'], x['installedMemory'],
                       x['installedFlash'], x['collectedSerialNumber'], x['collectedProductId'], x['productName'],
                       x['dimensionsFormat'], x['dimensions'], x['weight'], x['formFactor'], x['supportPage'],
                       x['visioStencilUrl'], x['smallImageUrl'], x['largeImageUrl'], x['baseProductId'],
                       x['productReleaseDate'], x['productDescription']]
            hardware.append(listing)

        csv_file = (csv_output_dir + cdm.filename('hardware.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareHeader)
            writer.writerows(hardware)
        print('Hardware List Done')
    else:
        print('Failed to get Hardware List')


# Function to retrieve a list of hardware EOL data
def get_hardware_eol(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/hardware-eol?customerId={customerid}'
    hardwareEOL = []
    hardwareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwType',
                         'currentHwEolMilestone', 'nextHwEolMilestone', 'hwInstanceId', 'productId',
                         'currentHwEolMilestoneDate', 'nextHwEolMilestoneDate', 'hwEolInstanceId']

    print("\nRetrieving Hardware EOL list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwType'],
                       x['currentHwEolMilestone'], x['nextHwEolMilestone'], x['hwInstanceId'], x['productId'],
                       x['currentHwEolMilestoneDate'], x['nextHwEolMilestoneDate'], x['hwEolInstanceId']]
            hardwareEOL.append(listing)

        csv_file = (csv_output_dir + cdm.filename('hardware_eol.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLHeader)
            writer.writerows(hardwareEOL)
        print('Hardware EOL List Done')
    else:
        print('Failed to get Hardware EOL List')


# Function to retrieve a list of hardware EOL bulletins
def get_hardware_eol_bulletins(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/hardware-eol-bulletins?customerId={customerid}'
    hardwareEOLBulletins = []
    hardwareEOLBulletinsHeader = ['customerid', 'customername', 'hwEolInstanceId', 'bulletinProductId',
                                  'bulletinNumber', 'bulletinTitle', 'eoLifeAnnouncementDate', 'eoSaleDate',
                                  'lastShipDate', 'eoSwMaintenanceReleasesDate', 'eoRoutineFailureAnalysisDate',
                                  'eoNewServiceAttachmentDate', 'eoServiceContractRenewalDate', 'lastDateOfSupport',
                                  'eoVulnerabilitySecuritySupport', 'url']

    print("\nRetrieving Hardware EOL Bulletins List....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['hwEolInstanceId'], x['bulletinProductId'], x['bulletinNumber'],
                       x['bulletinTitle'], x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['lastShipDate'],
                       x['eoSwMaintenanceReleasesDate'], x['eoRoutineFailureAnalysisDate'],
                       x['eoNewServiceAttachmentDate'], x['eoServiceContractRenewalDate'], x['lastDateOfSupport'],
                       x['eoVulnerabilitySecuritySupport'], x['url']]
            hardwareEOLBulletins.append(listing)

        csv_file = (csv_output_dir + cdm.filename('hardware_eol_bulletins.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLBulletinsHeader)
            writer.writerows(hardwareEOLBulletins)
        print('Hardware EOL Bulletins List Done')
    else:
        print('Failed to get Hardware EOL Bulletins List')


# Function to retrieve a list of software
def get_software(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}inventory/software?customerId={customerid}'
    software = []
    softwareHeader = ['customerid', 'customername', 'managedNeInstanceId', 'inventoryName', 'swType', 'swVersion',
                      'swMajorVersion', 'swCategory', 'swStatus', 'swName']

    print("\nRetrieving Software list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['managedNeInstanceId'], x['inventoryName'], x['swType'],
                       x['swVersion'], x['swMajorVersion'], x['swCategory'], x['swStatus'], x['swName']]
            software.append(listing)

        csv_file = (csv_output_dir + cdm.filename('software.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softwareHeader)
            writer.writerows(software)
        print('Software List Done')
    else:
        print('Failed to get Software List')


# Function to retrieve a list of software EOL data
def get_software_eol(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/software-eol?customerId={customerid}'
    softewareEOL = []
    softewareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'swType', 'currentSwEolMilestone', 'nextSwEolMilestone', 'swVersion',
                          'currentSwEolMilestoneDate', 'nextSwEolMilestoneDate', 'swEolInstanceId']

    print("\nRetrieving Software EOL list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'],
                       x['swType'], x['currentSwEolMilestone'], x['nextSwEolMilestone'], x['swVersion'],
                       x['currentSwEolMilestoneDate'], x['nextSwEolMilestoneDate'], x['swEolInstanceId']]
            softewareEOL.append(listing)

        csv_file = (csv_output_dir + cdm.filename('software_eol.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLHeader)
            writer.writerows(softewareEOL)
        print('Software EOL List Done')
    else:
        print('Failed to get Software EOL List!')


# Function to retrieve a list of software EOL bulletins
def get_software_eol_bulletins(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/software-eol-bulletins?customerId={customerid}'
    softewareEOLBulletins = []
    softewareEOLBulletinsHeader = ['customerid', 'customername', 'swEolInstanceId', 'bulletinNumber',
                                   'bulletinTitle', 'swMajorVersion', 'swMaintenanceVersion', 'swTrain', 'swType',
                                   'eoLifeAnnouncementDate', 'eoSaleDate', 'eoSwMaintenanceReleasesDate',
                                   'eoVulnerabilitySecuritySupport', 'lastDateOfSupport', 'url']

    print("\nRetrieving Software EOL Bulletins list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['swEolInstanceId'], x['bulletinNumber'], x['bulletinTitle'],
                       x['swMajorVersion'], x['swMaintenanceVersion'], x['swTrain'], x['swType'],
                       x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['eoSwMaintenanceReleasesDate'],
                       x['eoVulnerabilitySecuritySupport'], x['lastDateOfSupport'], x['url']]
            softewareEOLBulletins.append(listing)

        csv_file = (csv_output_dir + cdm.filename('software_eol_bulletins.csv'))
        with open(csv_file, 'w', encoding='UTF8',
                  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLBulletinsHeader)
            writer.writerows(softewareEOLBulletins)
        print('Software EOL Bulletins List Done')
    else:
        print('Failed to get Software EOL Bulletins List')


# Function to retrieve a list of field notices
def get_fieldnotices(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/field-notices?customerId={customerid}'
    fieldNotices = []
    fieldNoticesHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                          'vulnerabilityStatus', 'vulnerabilityReason', 'hwInstanceId', 'bulletinNumber']

    print("\nRetrieving Field Notices list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['vulnerabilityStatus'],
                       x['vulnerabilityReason'], x['hwInstanceId'], x['bulletinNumber']]
            fieldNotices.append(listing)

        csv_file = (csv_output_dir + cdm.filename('field_notices.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticesHeader)
            writer.writerows(fieldNotices)
        print('Field Notices List Done')
    else:
        print('Failed to get Field Notices List!')


# Function to retrieve a list of field notice bulletins
def get_fieldnoticebulletins(customerid, customername, csv_output_dir_dir):
    url = f'{urlBase}product-alerts/field-notice-bulletins?customerId={customerid}'
    fieldNoticeBulletins = []
    fieldNoticeBulletinsHeader = ['customerid', 'customername', 'bulletinFirstPublished', 'bulletinNumber',
                                  'fieldNoticeType', 'bulletinTitle', 'bulletinLastUpdated',
                                  'alertAutomationCaveat', 'url', 'bulletinSummary']

    print("\nRetrieving Field Notice Bulletins list....")
    jsonData = get_json_reply(url)
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['bulletinFirstPublished'], x['bulletinNumber'], x['fieldNoticeType'],
                       x['bulletinTitle'], x['bulletinLastUpdated'], x['alertAutomationCaveat'], x['url'],
                       x['bulletinSummary']]
            fieldNoticeBulletins.append(listing)

        csv_file = (csv_output_dir + cdm.filename('field_notice_bulletins.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticeBulletinsHeader)
            writer.writerows(fieldNoticeBulletins)
        print('Field Notice Bulletins List Done')
    else:
        print('Failed to get Field Notice Bulletins List!')


# Function to retrieve a list of security advisories
def get_security_advisory(customerid, customername, csv_output_dir_dir):
    print("\nRetrieving Security Advisory list....")
    url = f'{urlBase}product-alerts/security-advisories?customerId={customerid}'
    jsonData = get_json_reply(url)
    if jsonData:
        securityAdvisory = []
        securityAdvisoryHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwInstanceId',
                                  'vulnerabilityStatus', 'vulnerabilityReason', 'securityAdvisoryInstanceId']
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwInstanceId'],
                       x['vulnerabilityStatus'], x['vulnerabilityReason'], x['securityAdvisoryInstanceId']]
            securityAdvisory.append(listing)

        csv_file = (csv_output_dir + cdm.filename('security_advisory.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryHeader)
            writer.writerows(securityAdvisory)
        print('Security Advisory List Done')


# Function to retrieve a list of security advisory bulletins
def get_security_advisory_bulletins(customerid, customername, csv_output_dir_dir):
    print("\nRetrieving Security Advisory Bulletins list....")
    url = f'{urlBase}product-alerts/security-advisory-bulletins?customerId={customerid}'
    jsonData = get_json_reply(url)
    if jsonData:
        securityAdvisoryBulletins = []
        securityAdvisoryBulletinsHeader = ['customerid', 'customername', 'securityAdvisoryInstanceId', 'url',
                                           'bulletinVersion', 'advisoryId', 'bulletinTitle', 'bulletinFirstPublished',
                                           'bulletinLastUpdated', 'securityImpactRating', 'bulletinSummary',
                                           'alertAutomationCaveat', 'cveId', 'cvssBaseScore', 'cvssTemporalScore',
                                           'ciscoBugIds']
        for x in jsonData['data']:
            listing = [customerid, customername, x['securityAdvisoryInstanceId'], x['url'], x['bulletinVersion'],
                       x['advisoryId'], x['bulletinTitle'], x['bulletinFirstPublished'], x['bulletinLastUpdated'],
                       x['securityImpactRating'], x['bulletinSummary'], x['alertAutomationCaveat'], x['cveId'],
                       x['cvssBaseScore'], x['cvssTemporalScore'], x['ciscoBugIds']]
            securityAdvisoryBulletins.append(listing)

        csv_file = (csv_output_dir + cdm.filename('security_advisory_bulletins.csv'))
        with open(csv_file, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryBulletinsHeader)
            writer.writerows(securityAdvisoryBulletins)
        print('Security Advisory Bulletins List Done\n')


# Function to retrieve a list of customers
def get_customer_data():
    if scope == 0:
        logging.debug(f'Script Completed successfully')
        return True

    csv_file = (csv_output_dir + cdm.filename('customers.csv'))
    if os.path.exists(csv_file):
        print("\nRetrieving Customers Data....")
        with open(csv_file, 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']

                if scope == 1 or (scope == 2 and int(customer_id) == customerID):
                    get_all_data(str(customer_id), customer_name)
                    
            # end for
        # end with
        return True
    else:
        print("\nNo Customer Data to Retrieve....")
        return False
        
# Function to retrieve data for all customers
def get_all_data(customerid, customer):
    print(f'Scanning {customer}')
    csv_output_dir_dir = (csv_output_dir + customer + '_' + '/')
    os.mkdir(csv_output_dir_dir)
    get_contract_details(customerid, customer, csv_output_dir_dir)
    get_covered(customerid, customer, csv_output_dir_dir)
    get_not_covered(customerid, customer, csv_output_dir_dir)
    get_network_elements(customerid, customer, csv_output_dir_dir)
    get_inventory_groups(customerid, customer, csv_output_dir_dir)
    get_hardware(customerid, customer, csv_output_dir_dir)
    get_hardware_eol(customerid, customer, csv_output_dir_dir)
    get_hardware_eol_bulletins(customerid, customer, csv_output_dir_dir)
    get_software(customerid, customer, csv_output_dir_dir)
    get_software_eol(customerid, customer, csv_output_dir_dir)
    get_software_eol_bulletins(customerid, customer, csv_output_dir_dir)
    get_fieldnotices(customerid, customer, csv_output_dir_dir)
    get_fieldnoticebulletins(customerid, customer, csv_output_dir_dir)
    get_security_advisory(customerid, customer, csv_output_dir_dir)
    get_security_advisory_bulletins(customerid, customer, csv_output_dir_dir)


'''
Begin main application control
=======================================================================
'''
if __name__ == '__main__':
    count = 0

    # setup parser
    parser = argparse.ArgumentParser(description="Your script description.")
    parser.add_argument("customer", nargs='?', default='credentials', help="Customer name")
    parser.add_argument("-log", "--log-level", default="CRITICAL", help="Set the logging level (default: CRITICAL)")

    # Parse command-line arguments
    args = parser.parse_args()

    # setup the logging level
    logger = init_logger(args.log_level.upper())

    # call function to load config.ini data into variables
    customer = args.customer
    load_config(customer)

    # create a per-customer folder for saving data
    if customer:
        # Create the customers directory
        os.makedirs(customer, exist_ok=True)
        # Change into the directory
        os.chdir(customer)

    print(f'Script will execute {testloop} time(s)')
    while count < testloop:
        count += 1

        # setup file logging if desired
        init_debug_file(count)

        print(f'Execution:{count} of {testloop}')
        cdm.storage(csv_output_dir, None, None)
        cdm.token()

        status = get_customers()
        if status: status = get_customer_data()

        logging.debug(f'Script Completed {count} time(s) Success:{status}')
        print(f'Script Completed {count} time(s) Success:{status}')

        # pause between each itteration
        if count < testloop:
            print('\n\npausing for 2 secs')
            logging.debug('=================================================================')
            time.sleep(2)
    # end for

