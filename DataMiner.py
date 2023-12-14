# import library to use HTTP and JSON request
import os
import shutil
import requests
import csv
import time
import math
from configparser import ConfigParser
from requests.exceptions import Timeout
import random
import logging

# Data Initializer Variables
token = ''
tokenStartTime = 0
clientId = ''
clientSecret = ''
csv_output = 'outputcsv/'
scope = '1'
customerID = 0
debug = 0
configFile = 'config.ini'
fmt = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
logfile = 'SNTC_DataMiner_log.txt'
tokenUrl = ''
baseUrl = ''
loopCount = 0
urlTimeout = 0


# Function to load configuration from config.ini and continue or create a template if not found and exit
def load_config():
    global clientId
    global clientSecret
    global scope
    global customerID
    global debug
    global tokenUrl
    global baseUrl
    global loopCount
    global urlTimeout
    if os.path.isfile(logfile):
        os.remove(logfile)
    config = ConfigParser()
    if os.path.isfile(configFile):
        print('Config.ini file was found, continuing...')
        config.read(configFile)
        clientId = (config['credentials']['client_id'])
        clientSecret = (config['credentials']['client_secret'])
        scope = int((config['settings']['scope']))
        customerID = int((config['settings']['customerID']))
        debug = int((config['settings']['debug']))
        tokenUrl = (config['settings']['tokenUrl'])
        baseUrl = (config['settings']['baseUrl'])
        loopCount = int((config['settings']['loopCount']))
        urlTimeout = int((config['settings']['urlTimeout']))
    else:
        print('Config.ini not found!!!!!!!!!!!!\nCreating config.ini...')
        print('\nNOTE: you must edit the config.ini file with your information\nExiting...')
        config.add_section('credentials')
        config.set('credentials', 'client_id', 'client_id')
        config.set('credentials', 'client_secret', 'client_secret')
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
        config.set('settings', 'loopCount', '1')
        config.set('settings', '# Set how many second to wait for the API to respond default', '10')
        config.set('settings', 'urlTimeout', '10')

        with open(configFile, 'w') as configfile:
            config.write(configfile)
        input("Press Enter to continue...")
        exit()


# Function to generate or clear output folders for use.

def temp_storage():
    if os.path.isdir(csv_output):
        shutil.rmtree(csv_output)
        os.mkdir(csv_output)
    else:
        os.mkdir(csv_output)
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S", filename=logfile)


# Function to check token lifecycle not to exceed 60 mins
def token_time_check():
    checkTime = time.time()
    tokenTime = math.ceil(int(checkTime - tokenStartTime) / 60)
    if tokenTime > 50:
        get_sntc_token()


# Function to get valid API token from SNTC
def get_sntc_token():
    global token
    global tokenStartTime
    print('\nGetting SNTC Token')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = tokenUrl
    querystring = {'grant_type': 'client_credentials',
                   'client_id': clientId,
                   'client_secret': clientSecret}
    token_response = requests.request('POST', url, headers=headers, params=querystring).json()

    print('Retrieved token')
    try:
        token = (token_response['access_token'])
    except KeyError:
        token = ""
        pass
    tokenStartTime = time.time()
    if len(token) > 0:
        print("Done!")
    else:
        print("Unable to retrieve a valid token\n"
              "Check config.ini and check your API Keys for accuracy")
        print(f"Client ID: {clientId}")
        print(f"Client Secret: {clientSecret}")
        exit()


# Function to retrieve raw data from endpoint
def get_json_data(url):
    tries = 1
    response = []
    while True:
        try:
            token_time_check()
            headers = {
                'Authorization': f'Bearer {token}'}
            max_attempts = 20
            attempts = 0
            while attempts < max_attempts:
                # Make a request to API
                for i in range(max_attempts):
                    try:
                        response = requests.request("GET", url, headers=headers, verify=True, timeout=urlTimeout)
                        logging.debug(f'URL Request: {url}')
                        logging.debug(f'HTTP Code:{response.status_code}')
                        logging.debug(f'Review API Headers:{response.headers}')
                        logging.debug(f'Response Body:{response.content}')
                        if i == 0:
                            logging.debug(f'Collection was successful')
                        else:
                            logging.debug(f'Collection retry # {i + 1} was successful')
                            print(f'Collection retry # {i + 1} was successful')
                        break
                    except Timeout:
                        logging.debug(f'Time out error getting data')
                        logging.debug(f'Retrying ...')
                        print(f'Time out error getting data')
                        print(f'Retrying ...')
                        time.sleep(random.random())
                # If not rate limited, break out of while loop and continue
                if response.status_code == 200:
                    break
                attempts += 1
            reply = response.json()
            if debug == 1:
                logging.debug(reply)
            if response.status_code == 500:
                logging.debug("URL Request:", url,
                              "\nHTTP Code:", response.status_code,
                              "\nReview API Headers:", response.headers,
                              "\nResponse Body:", response.content)
                logging.debug("Error retrieving API response")
            if response.text.__contains__('Customer Id is not associated with Partner'):
                logging.debug('Customer is not associated with Partner')
                break
            try:
                if response.status_code == 200:
                    if len(reply) > 0:
                        if tries >= 2:
                            logging.debug("\nSuccess on retry! \nContinuing.\n")
                        return reply
            finally:
                if response.status_code == 200:
                    return reply
        except Exception as Error:
            if response.status_code == 500 or response.status_code == 400:
                logging.debug("Error retrieving API response")
                logging.debug("\nResponse Content:", response.content)
                logging.debug("\nAttempt #", tries, "Failed getting:", Error,
                              "\nRetrying in", 1, "seconds\n")
                time.sleep(1)
                if tries >= 3:
                    break
        finally:
            tries += 1


# Function to retrieve a list of customers
def get_customers():
    print("\nRetrieving Customer list....")
    url = f'{baseUrl}customer-info/customer-details'
    jsonData = get_json_data(url)
    customers = []
    customerHeader = ['customerId', 'customerName', 'streetAddress1', 'streetAddress2', 'streetAddress3',
                      'streetAddress4',
                      'city', 'state', 'country', 'zipCode', 'theaterCode']
    for x in jsonData['data']:
        listing = [x['customerId'], x['customerName'], x['streetAddress1'], x['streetAddress2'],
                   x['streetAddress3'], x['streetAddress4'], x['city'], x['state'], x['country'], x['zipCode'],
                   x['theaterCode']]
        logging.debug(f'Found customer {listing[1]}')
        customers.append(listing)
    with open(csv_output + 'customers.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(customerHeader)
        writer.writerows(customers)
    print('Customer List Done!')


# Function to retrieve a list of contracts
def get_contract_details(customerid, customername, csv_output_dir):
    print("\nRetrieving Contract Details....")
    url = f'{baseUrl}contracts/contract-details?customerId={customerid}'
    jsonData = get_json_data(url)
    contracts = []
    contractsHeader = ['customerid', 'customername', 'contractNumber', 'contractStatus', 'contractStartDate',
                       'contractEndDate', 'serviceProgram', 'serviceLevel', 'billtoSiteId', 'billtoSiteName',
                       'billtoAddressLine1', 'billtoAddressLine2', 'billtoAddressLine3', 'billtoAddressLine4',
                       'billtoCity', 'billtoState', 'billtoPostalCode', 'billtoProvince', 'billtoCountry',
                       'billtoGuName', 'siteUseName', 'siteUseId', 'siteAddress1', 'siteCity', 'siteStateProvince',
                       'sitePostalCode', 'siteCountry', 'baseProductId']
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
        with open(csv_output_dir + 'contracts.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(contractsHeader)
            writer.writerows(contracts)
        print('Contract List Done')


# Function to retrieve a list of devices covered
def get_covered(customerid, customername, csv_output_dir):
    print("\nRetrieving Covered list....")
    url = f'{baseUrl}contracts/coverage?customerId={customerid}'
    jsonData = get_json_data(url)
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
        with open(csv_output_dir + 'covered.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(coveredHeader)
            writer.writerows(covered)
        print('Covered List Done')


# Function to retrieve a list of devices that are not covered under a contract
def get_not_covered(customerid, customername, csv_output_dir):
    print("\nRetrieving Not Covered list....")
    url = f'{baseUrl}contracts/not-covered?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        notcovered = []
        notcoveredHeader = ['customerid', 'customername', 'contractInstanceNumber', 'serialNumber', 'productId',
                            'hwType', 'orderShipDate', 'installedatSiteId', 'installedatSiteName',
                            'installedatAddressLine1', 'installedatAddressLine2', 'installedatAddressLine3',
                            'installedatAddressLine4', 'installedatCity', 'installedatState', 'installedatPostalCode',
                            'installedatProvince', 'installedatCountry', 'warrantyType', 'warrantyStartDate',
                            'warrantyEndDate', 'neInstanceId', 'billtoPartyId']
        for x in jsonData['data']:
            listing = [customerid, customername, x['contractInstanceNumber'], x['serialNumber'], x['productId'],
                       x['hwType'], x['orderShipDate'], x['installedatSiteId'], x['installedatSiteName'],
                       x['installedatAddressLine1'], x['installedatAddressLine2'], x['installedatAddressLine3'],
                       x['installedatAddressLine4'], x['installedatCity'], x['installedatState'],
                       x['installedatPostalCode'], x['installedatProvince'], x['installedatCountry'], x['warrantyType'],
                       x['warrantyStartDate'], x['warrantyEndDate'], x['neInstanceId'], x['billtoPartyId']]
            notcovered.append(listing)
        with open(csv_output_dir + 'not_covered.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(notcoveredHeader)
            writer.writerows(notcovered)
        print('Not Covered List Done')


# Function to retrieve a list of network elements
def get_network_elements(customerid, customername, csv_output_dir):
    print("\nRetrieving Network Elements list....")
    url = f'{baseUrl}inventory/network-elements?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        networkElements = []
        networkElementsHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                                 'managementAddress', 'neSubtype', 'inventoryAvailability', 'lastConfigRegister',
                                 'ipAddress', 'hostname', 'sysName', 'featureSet', 'inventoryCollectionDate',
                                 'productFamily', 'productId', 'productType', 'createDate', 'swType', 'swVersion',
                                 'reachabilityStatus', 'neType', 'lastReset', 'resetReason', 'sysContact', 'sysDescr',
                                 'sysLocation', 'sysObjectId', 'configRegister', 'configAvailability',
                                 'configCollectionDate', 'imageName', 'bootstrapVersion', 'isManagedNe', 'userField1',
                                 'userField2', 'userField3', 'userField4', 'macAddress']
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
        with open(csv_output_dir + 'network_elements.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(networkElementsHeader)
            writer.writerows(networkElements)
        print('Network Elements List Done')


# Function to retrieve a list of inventory groups
def get_inventory_groups(customerid, customername, csv_output_dir):
    print("\nRetrieving Inventory Groups list....")
    url = f'{baseUrl}customer-info/inventory-groups?customerId={customerid}'
    jsonData = get_json_data(url)
    inventory = []
    inventoryHeader = ['customerId', 'customerName', 'inventoryId', 'inventoryName']
    if jsonData:
        for x in jsonData['data']:
            listing = [customerid, customername, x['inventoryId'], x['inventoryName']]
            inventory.append(listing)
        with open(csv_output_dir + 'inventory.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(inventoryHeader)
            writer.writerows(inventory)
        print('Inventory List Done')


# Function to retrieve a list of hardware
def get_hardware(customerid, customername, csv_output_dir):
    print("\nRetrieving Hardware list....")
    url = f'{baseUrl}inventory/hardware?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        hardware = []
        hardwareHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'inventoryName',
                          'hwInstanceId', 'hwName', 'hwType', 'productSubtype', 'slot', 'productFamily', 'productId',
                          'productType', 'swVersion', 'serialNumber', 'serialNumberStatus', 'hwRevision', 'tan',
                          'tanRevision', 'pcbNumber', 'installedMemory', 'installedFlash', 'collectedSerialNumber',
                          'collectedProductId', 'productName', 'dimensionsFormat', 'dimensions', 'weight',
                          'formFactor', 'supportPage', 'visioStencilUrl', 'smallImageUrl', 'largeImageUrl',
                          'baseProductId', 'productReleaseDate', 'productDescription']
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
        with open(csv_output_dir + 'hardware.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareHeader)
            writer.writerows(hardware)
        print('Hardware List Done')


# Function to retrieve a list of hardware EOL data
def get_hardware_eol(customerid, customername, csv_output_dir):
    print("\nRetrieving Hardware EOL list....")
    url = f'{baseUrl}product-alerts/hardware-eol?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        hardwareEOL = []
        hardwareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwType',
                             'currentHwEolMilestone', 'nextHwEolMilestone', 'hwInstanceId', 'productId',
                             'currentHwEolMilestoneDate', 'nextHwEolMilestoneDate', 'hwEolInstanceId']
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwType'],
                       x['currentHwEolMilestone'], x['nextHwEolMilestone'], x['hwInstanceId'], x['productId'],
                       x['currentHwEolMilestoneDate'], x['nextHwEolMilestoneDate'], x['hwEolInstanceId']]
            hardwareEOL.append(listing)
        with open(csv_output_dir + 'hardware_eol.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLHeader)
            writer.writerows(hardwareEOL)
        print('Hardware EOL List Done')


# Function to retrieve a list of hardware EOL bulletins
def get_hardware_eol_bulletins(customerid, customername, csv_output_dir):
    print("\nRetrieving Hardware EOL Bulletins List....")
    url = f'{baseUrl}product-alerts/hardware-eol-bulletins?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        hardwareEOLBulletins = []
        hardwareEOLBulletinsHeader = ['customerid', 'customername', 'hwEolInstanceId', 'bulletinProductId',
                                      'bulletinNumber', 'bulletinTitle', 'eoLifeAnnouncementDate', 'eoSaleDate',
                                      'lastShipDate', 'eoSwMaintenanceReleasesDate', 'eoRoutineFailureAnalysisDate',
                                      'eoNewServiceAttachmentDate', 'eoServiceContractRenewalDate', 'lastDateOfSupport',
                                      'eoVulnerabilitySecuritySupport', 'url']
        for x in jsonData['data']:
            listing = [customerid, customername, x['hwEolInstanceId'], x['bulletinProductId'], x['bulletinNumber'],
                       x['bulletinTitle'], x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['lastShipDate'],
                       x['eoSwMaintenanceReleasesDate'], x['eoRoutineFailureAnalysisDate'],
                       x['eoNewServiceAttachmentDate'], x['eoServiceContractRenewalDate'], x['lastDateOfSupport'],
                       x['eoVulnerabilitySecuritySupport'], x['url']]
            hardwareEOLBulletins.append(listing)
        with open(csv_output_dir + 'hardware_eol_bulletins.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(hardwareEOLBulletinsHeader)
            writer.writerows(hardwareEOLBulletins)
        print('Hardware EOL Bulletins List Done')


# Function to retrieve a list of software
def get_software(customerid, customername, csv_output_dir):
    print("\nRetrieving Software list....")
    url = f'{baseUrl}inventory/software?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        software = []
        softwareHeader = ['customerid', 'customername', 'managedNeInstanceId', 'inventoryName', 'swType', 'swVersion',
                          'swMajorVersion', 'swCategory', 'swStatus', 'swName']
        for x in jsonData['data']:
            listing = [customerid, customername, x['managedNeInstanceId'], x['inventoryName'], x['swType'],
                       x['swVersion'], x['swMajorVersion'], x['swCategory'], x['swStatus'], x['swName']]
            software.append(listing)
        with open(csv_output_dir + 'software.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softwareHeader)
            writer.writerows(software)
        print('Software List Done')


# Function to retrieve a list of software EOL data
def get_software_eol(customerid, customername, csv_output_dir):
    print("\nRetrieving Software EOL list....")
    url = f'{baseUrl}product-alerts/software-eol?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        softewareEOL = []
        softewareEOLHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                              'swType', 'currentSwEolMilestone', 'nextSwEolMilestone', 'swVersion',
                              'currentSwEolMilestoneDate', 'nextSwEolMilestoneDate', 'swEolInstanceId']
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'],
                       x['swType'], x['currentSwEolMilestone'], x['nextSwEolMilestone'], x['swVersion'],
                       x['currentSwEolMilestoneDate'], x['nextSwEolMilestoneDate'], x['swEolInstanceId']]
            softewareEOL.append(listing)
        with open(csv_output_dir + 'software_eol.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLHeader)
            writer.writerows(softewareEOL)
        print('Software EOL List Done')


# Function to retrieve a list of software EOL bulletins
def get_software_eol_bulletins(customerid, customername, csv_output_dir):
    print("\nRetrieving Software EOL Bulletins list....")
    url = f'{baseUrl}product-alerts/software-eol-bulletins?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        softewareEOLBulletins = []
        softewareEOLBulletinsHeader = ['customerid', 'customername', 'swEolInstanceId', 'bulletinNumber',
                                       'bulletinTitle', 'swMajorVersion', 'swMaintenanceVersion', 'swTrain', 'swType',
                                       'eoLifeAnnouncementDate', 'eoSaleDate', 'eoSwMaintenanceReleasesDate',
                                       'eoVulnerabilitySecuritySupport', 'lastDateOfSupport', 'url']
        for x in jsonData['data']:
            listing = [customerid, customername, x['swEolInstanceId'], x['bulletinNumber'], x['bulletinTitle'],
                       x['swMajorVersion'], x['swMaintenanceVersion'], x['swTrain'], x['swType'],
                       x['eoLifeAnnouncementDate'], x['eoSaleDate'], x['eoSwMaintenanceReleasesDate'],
                       x['eoVulnerabilitySecuritySupport'], x['lastDateOfSupport'], x['url']]
            softewareEOLBulletins.append(listing)
        with open(csv_output_dir + 'software_eol_bulletins.csv', 'w', encoding='UTF8',
                  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(softewareEOLBulletinsHeader)
            writer.writerows(softewareEOLBulletins)
        print('Software EOL Bulletins List Done')


# Function to retrieve a list of field notices
def get_fieldnotices(customerid, customername, csv_output_dir):
    print("\nRetrieving Field Notices list....")
    url = f'{baseUrl}product-alerts/field-notices?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        fieldNotices = []
        fieldNoticesHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId',
                              'vulnerabilityStatus', 'vulnerabilityReason', 'hwInstanceId', 'bulletinNumber']
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['vulnerabilityStatus'],
                       x['vulnerabilityReason'], x['hwInstanceId'], x['bulletinNumber']]
            fieldNotices.append(listing)
        with open(csv_output_dir + 'field_notices.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticesHeader)
            writer.writerows(fieldNotices)
        print('Field Notices List Done')


# Function to retrieve a list of field notice bulletins
def get_fieldnoticebulletins(customerid, customername, csv_output_dir):
    print("\nRetrieving Field Notice Bulletins list....")
    url = f'{baseUrl}product-alerts/field-notice-bulletins?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        fieldNoticeBulletins = []
        fieldNoticeBulletinsHeader = ['customerid', 'customername', 'bulletinFirstPublished', 'bulletinNumber',
                                      'fieldNoticeType', 'bulletinTitle', 'bulletinLastUpdated',
                                      'alertAutomationCaveat', 'url', 'bulletinSummary']
        for x in jsonData['data']:
            listing = [customerid, customername, x['bulletinFirstPublished'], x['bulletinNumber'], x['fieldNoticeType'],
                       x['bulletinTitle'], x['bulletinLastUpdated'], x['alertAutomationCaveat'], x['url'],
                       x['bulletinSummary']]
            fieldNoticeBulletins.append(listing)
        with open(csv_output_dir + 'field_notice_bulletins.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldNoticeBulletinsHeader)
            writer.writerows(fieldNoticeBulletins)
        print('Field Notice Bulletins List Done')


# Function to retrieve a list of security advisories
def get_security_advisory(customerid, customername, csv_output_dir):
    print("\nRetrieving Security Advisory list....")
    url = f'{baseUrl}product-alerts/security-advisories?customerId={customerid}'
    jsonData = get_json_data(url)
    if jsonData:
        securityAdvisory = []
        securityAdvisoryHeader = ['customerid', 'customername', 'neInstanceId', 'managedNeInstanceId', 'hwInstanceId',
                                  'vulnerabilityStatus', 'vulnerabilityReason', 'securityAdvisoryInstanceId']
        for x in jsonData['data']:
            listing = [customerid, customername, x['neInstanceId'], x['managedNeInstanceId'], x['hwInstanceId'],
                       x['vulnerabilityStatus'], x['vulnerabilityReason'], x['securityAdvisoryInstanceId']]
            securityAdvisory.append(listing)
        with open(csv_output_dir + 'security_advisory.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryHeader)
            writer.writerows(securityAdvisory)
        print('Security Advisory List Done')


# Function to retrieve a list of security advisory bulletins
def get_security_advisory_bulletins(customerid, customername, csv_output_dir):
    print("\nRetrieving Security Advisory Bulletins list....")
    url = f'{baseUrl}product-alerts/security-advisory-bulletins?customerId={customerid}'
    jsonData = get_json_data(url)
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
        with open(csv_output_dir + 'security_advisory_bulletins.csv', 'w', encoding='UTF8',
                  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(securityAdvisoryBulletinsHeader)
            writer.writerows(securityAdvisoryBulletins)
        print('Security Advisory Bulletins List Done\n')


# Function to retrieve a list of customers
def get_customer_data():
    print("\nRetrieving Customers Data....")
    if scope == 0:
        logging.debug(f'Script Completed successfully')
        exit()
    elif scope == 1:
        with open(csv_output + 'customers.csv', 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']
                get_all_data(customerId, customer)
    elif scope == 2:
        with open(csv_output + 'customers.csv', 'r') as customers:
            customerList = csv.DictReader(customers)
            for row in customerList:
                customerId = row['customerId']
                customer = row['customerName']
                if int(customerId) == customerID:
                    get_all_data(str(customerId), customer)


# Function to retrieve data for all customers
def get_all_data(customerid, customer):
    print(f'Scanning {customer}')
    csv_output_dir = (csv_output + customer + '_' + '/')
    os.mkdir(csv_output_dir)
    get_contract_details(customerid, customer, csv_output_dir)
    get_covered(customerid, customer, csv_output_dir)
    get_not_covered(customerid, customer, csv_output_dir)
    get_network_elements(customerid, customer, csv_output_dir)
    get_inventory_groups(customerid, customer, csv_output_dir)
    get_hardware(customerid, customer, csv_output_dir)
    get_hardware_eol(customerid, customer, csv_output_dir)
    get_hardware_eol_bulletins(customerid, customer, csv_output_dir)
    get_software(customerid, customer, csv_output_dir)
    get_software_eol(customerid, customer, csv_output_dir)
    get_software_eol_bulletins(customerid, customer, csv_output_dir)
    get_fieldnotices(customerid, customer, csv_output_dir)
    get_fieldnoticebulletins(customerid, customer, csv_output_dir)
    get_security_advisory(customerid, customer, csv_output_dir)
    get_security_advisory_bulletins(customerid, customer, csv_output_dir)


# Main branch
load_config()
print(f'\nScript is executing {loopCount} Time(s)')
for count in range(0, loopCount):
    print(f'Execution:{count + 1} of {loopCount}')
    temp_storage()
    get_sntc_token()
    get_customers()
    get_customer_data()
    logging.debug(f'Script Completed {count + 1} time(s) successfully')
    print(f'Script Completed {count + 1} time(s) successfully')
    if count + 1 == loopCount:
        # Clean exit
        exit()
    else:
        # pause 5 sec between each itteration
        print('\n\npausing for 2 secs')
        logging.debug('=================================================================')
        time.sleep(2)
