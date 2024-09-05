#
# Donnie V Savage  |  Principle Marketing Engineer  |  RAY ALLEN, Inc.
# donnie.savage@rayalleninc.com  |  www.rayalleninc.com
#
"""
Some SNTC Data Available
    A. Customers *
    B. Success Tracks *
    C. Customer Data Reports
        A. Assets *
        B. Hardware *
        C. Software *
        D. Security Advisories *
        E. Field Notices *
        F. Priority Bugs *
        G. Purchased Licenses *
        H. Licenses with Assets *

No SNT Data Available
    D. Contracts
       Contract Details *
       Partner Offers *
       Partner Offer Sessions *
       Customer Lifecycle *

    E. Optimal Software Version
        A. Software Groups *
        B. Software Group suggestions *
        C. Software Group suggestions-Assets *
        D. Software Group suggestions-Bug List *
        E. Software Group suggestions-Field Notices *
        F. Software Group suggestions-Advisories *

    F. Automated Fault Management
        A. Faults *
        B. Fault Summary *
        C. Affected Assets *

    G. Regulatory Compliance Check
        A. Compliance Violations *
        B. Assets violating compliance rule *
        C. Policy Rule Details *
        D. Compliance Suggestions *
        E. Assets with violations *
        F. Asset Violations *
        G. Obtained *

    H. Risk Mitigation Check
        A. Crash Risk Assets *
        B. Crash Risk Factors *
        C. Similar Assets *
        D. Assets Crashed in last 1d, 7d, 15d, 90d *
        E. Asset Crash History *
"""
#
# Process SNTC files and make them look like PCX files where posiable...
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
import pandas as pd

import argparse
from configparser import ConfigParser

# SNTC debugging settings
# =======================================================================
# Logging Variables
fmt = "%(asctime)s %(name)10s %(levelname)8s: %(message)s"
logfile = 'SNTC_log.txt'

# Define a mapping of log level strings to logging levels
DEBUG	 = 'DEBUG'
INFO	 = 'INFO'
WARNING  = 'WARNING'
ERROR	 = 'ERROR'
CRITICAL = 'CRITICAL'

# Debug Variables
codeVersion = str("2.0.0-d")
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

# CSV FileNames
pcx_csv_usecases			= '../Cisco-UseCases.csv'

pcx_csv_customers			= (csv_output_dir + 'Customers.csv')
pcx_csv_allCustomers			= (csv_output_dir + 'All_Customers.csv')
pcx_csv_successTracks			= (csv_output_dir + 'Success_Track.csv')
pcx_csv_lifecycle			= (csv_output_dir + 'Lifecycle.csv')

pcx_csv_contracts			= (csv_output_dir + 'Contracts.csv')
pcx_csv_contractsDetails		= (csv_output_dir + 'Contract_Details.csv')
pcx_csv_contractsWithCustomers		= (csv_output_dir + 'Contracts_With_Customer_Names.csv')
pcx_csv_contractsL2			= (csv_output_dir + 'L2_contracts.csv')

pcx_csv_partnerOffers			= (csv_output_dir + 'Partner_Offers.csv')
pcx_csv_partnerOfferSessions		= (csv_output_dir + 'Partner_Offer_Sessions.csv')

pcx_csv_assets				= (csv_output_dir + 'Assets.csv')
pcx_csv_hardware			= (csv_output_dir + 'Hardware.csv')
pcx_csv_software			= (csv_output_dir + 'Software.csv')

pcx_csv_purchasedLicenses		= (csv_output_dir + 'Purchased_Licenses.csv')
pcx_csv_licenses			= (csv_output_dir + 'Licenses_with_assets.csv')

pcx_csv_priorityBugs			= (csv_output_dir + 'Priority_Bugs.csv')
pcx_csv_fieldNotices			= (csv_output_dir + 'Field_Notices.csv')
pcx_csv_securityAdvisories		= (csv_output_dir + 'Security_Advisories.csv')

pcx_csv_RCCObtained			= (csv_output_dir + 'Regulatory_Compliance_Obtained.csv')
pcx_csv_RCCComplianceViolations		= (csv_output_dir + 'Regulatory_Compliance_Violations.csv')
pcx_csv_RCCAssetsViolatingComplianceRule= (csv_output_dir + 'Regulatory_Compliance_Assets_Violating_Compliance_Rule.csv')
pcx_csv_RCCPolicyRuleDetails		= (csv_output_dir + 'Regulatory_Compliance_Policy_Rule_Details.csv')
pcx_csv_RCCComplianceSuggestions	= (csv_output_dir + 'Regulatory_Compliance_Suggestions.csv')
pcx_csv_RCCAssetsWithViolations		= (csv_output_dir + 'Regulatory_Compliance_Assets_With_Violations.csv')
pcx_csv_RCCAssetViolations		= (csv_output_dir + 'Regulatory_Compliance_Asset_Violations.csv')

pcx_csv_SWGroups			= (csv_output_dir + 'Software_Groups.csv')
pcx_csv_SWGroupSuggestionsTrend		= (csv_output_dir + 'Software_Group_Suggestions_Trend.csv')
pcx_csv_SWGroupSuggestionSummaries	= (csv_output_dir + 'Software_Group_Suggestions_Summaries.csv')
pcx_csv_SWGroupSuggestionsReleases	= (csv_output_dir + 'Software_Group_Suggestions_Releases.csv')
pcx_csv_SWGroupSuggestionAssets		= (csv_output_dir + 'Software_Group_Suggestion_Assets.csv')
pcx_csv_SWGroupSuggestionsBugList	= (csv_output_dir + 'Software_Group_Suggestion_Bug_List.csv')
pcx_csv_SWGroupSuggestionsFieldNotices	= (csv_output_dir + 'Software_Group_Suggestion_Field_Notices.csv')
pcx_csv_SWGroupSuggestionsAdvisories	= (csv_output_dir + 'Software_Group_Suggestion_Security_Advisories.csv')

pcx_csv_AFMOSV_List			= (csv_output_dir + 'OSV_AFM_List.csv')
pcx_csv_AFMFaults			= (csv_output_dir + 'Automated_Fault_Management_Faults.csv')
pcx_csv_AFMFaultSummary			= (csv_output_dir + 'Automated_Fault_Management_Fault_Summary.csv')
pcx_csv_AFMFaultAffectedAssets		= (csv_output_dir + 'Automated_Fault_Management_Fault_Affected_Assets.csv')
pcx_csv_AFMFaultHistory			= (csv_output_dir + 'Automated_Fault_Management_Fault_History.csv')

pcx_csv_CrashRiskAssets			= (csv_output_dir + 'Crash_Risk_Assets.csv')
pcx_csv_CrashRiskFactors		= (csv_output_dir + 'Crash_Risk_Factors.csv')
pcx_csv_CrashRiskSimilarAssets		= (csv_output_dir + 'Crash_Risk_Similar_Assets.csv')
pcx_csv_CrashRiskAssetsLastCrashed	= (csv_output_dir + 'Crash_Risk_Assets_Last_Crashed.csv')
pcx_csv_CrashRiskAssetCrashHistory	= (csv_output_dir + 'Crash_Risk_Asset_Crash_History.csv')

ciscoUseCases = []
ciscoSuccessTracks = [
    "38396885",
    "40317380",
    "40485321",
    "40636840",
    "50320048",
    "50949451",
    "52517223"
    ]

customerSuccessTracks = [
    {"id": "40636840", "access": False},
    {"id": "38396885", "access": False},
    {"id": "52517223", "access": False},
    {"id": "40317380", "access": False},
    {"id": "50949451", "access": False},
    {"id": "50320048", "access": False},
    {"id": "40485321", "access": False}
]

assetData  = {}
hwInfoData = {}
swInfoData = {}
hwEOLData  = {}
swEOLData  = {}

'''
Begin defining functions
=======================================================================
'''
# Function to generate or clear output and temp folders for use.
def temp_storage():
    if os.path.isdir(csv_output_dir):
        shutil.rmtree(csv_output_dir)
    os.mkdir(csv_output_dir)

    if os.path.isdir(json_output_dir):
        shutil.rmtree(json_output_dir)
    os.mkdir(json_output_dir)

    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

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

    # Setup log storage - incase needed
    if os.path.isdir(log_output_dir):
        shutil.rmtree(log_output_dir)
    os.mkdir(log_output_dir)
    
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
def usage():
    print(f"Usage: python3 {sys.argv[0]} <partner> -log=<LOG_LEVEL>")
    print(f"Args:")
    print(f"   Required folder name holding Partner's SNTC Data.\n")
    sys.exit()

####
## Wrapper functions to read per customer device related CSV files
#
# SNTC Hardware_EOL.csv Header
#	customerid, customername, neInstanceId, managedNeInstanceId
#	hwType, currentHwEolMilestone, nextHwEolMilestone, hwInstanceId, productId
#	currentHwEolMilestoneDate, nextHwEolMilestoneDate, hwEolInstanceId
def read_device_hwEOLInfo(customer, partner):
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Hardware_EOL.csv'
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

#
# SNTC Software_EOL.csv Header
#	customerid, customername, neInstanceId, managedNeInstanceId
#	swType, currentSwEolMilestone, nextSwEolMilestone, swVersion,
#	currentSwEolMilestoneDate, nextSwEolMilestoneDate, swEolInstanceId
def read_device_swEOLInfo(customer, partner):
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Software_EOL.csv'
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

# SNTC Hardware.csv Header
#	customerid, customername, neInstanceId, managedNeInstanceId
#	inventoryName, hwInstanceId, hwName, hwType, productSubtype, slot
#	productFamily, productId, productType, swVersion, serialNumber, serialNumberStatus
#	hwRevision, tan, tanRevision, pcbNumber, installedMemory, installedFlash
#	collectedSerialNumber, collectedProductId, productName
#	dimensionsFormat, dimensions, weight, formFactor, supportPage, visioStencilUrl
#	smallImageUrl, largeImageUrl, baseProductId, productReleaseDate, productDescription
def read_device_hwInfo(customer, partner):
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    filename = f'{sntc_dir}{partner}/{customerName}/csv/{customerId}_Hardware.csv'
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

# SNTC Software.csv Header
#	customerid, customername, managedNeInstanceId, inventoryName,
#	swType, swVersion, swMajorVersion, swCategory, swStatus, swName
def read_device_swInfo(customer, partner):
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    filename = f'{sntc_dir}{partner}/{customerName}/csv/{customerId}_Software.csv'
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

# SNTC Assets.csv Header
#	customerid, customername, neInstanceId, managedNeInstanceId
#	inventoryName, managementAddress, neSubtype, inventoryAvailability, lastConfigRegister
#	ipAddress, hostname, sysName, featureSet, inventoryCollectionDate, productFamily, productId, productType, createDate
#	swType, swVersion, reachabilityStatus, neType, lastReset, resetReason,
#	sysContact, sysDescr, sysLocation, sysObjectId, configRegister, configAvailability, configCollectionDate,
#	imageName, bootstrapVersion, isManagedNe, userField1, userField2, userField3, userField4, macAddress
def read_device_assets(customer, partner):
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    filename = f'{sntc_dir}{partner}/{customerName}/csv/{customerId}_Assets.csv'
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

####
## Wrapper function to read CSV files
def read_csv_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader)
            rows = [row for row in reader]
        return rows
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

def read_csv_dict(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader]
        return rows
    except FileNotFoundError:
        logger(ERROR, f"File:{filename} does not exist")
        return None

# Function to save JSON files
def save_json_file(items, filename):
    with open(filename, 'w') as json_file:
        json.dump(items, json_file, indent=4)
    logging.info(f'JSON {filename}: Saved')

# Function to create an empty dictonary
def init_pcxData(CSV_Header, customerId):
    pcx = {key: "" for key in CSV_Header.split(',')}
    pcx['customerId']		= customerId
    return pcx

# Function to create an empty list
def blank_list(size):
    list =  [''] * size + ['\n']
    return list

######################################################################
################## Start of functions to process customers ###########
######################################################################
#
def find_device_security_cnt(sec_advisories, hwInstanceId):
    count = 0
    for sec_advisory in sec_advisories:
        if sec_advisory['hwInstanceId'] == hwInstanceId:
            count += 1
    return count

def find_device_advisory_cnt(neInstanceId):
    count = 0
    logger(DEBUG, f'find_device_advisory_cnt: STUB')
    return count

def find_device_by_neId(listData, neInstanceId):
    for list in listData:
        if list['neInstanceId'] == neInstanceId:
            return list
    logger(DEBUG, f'list not found for {neInstanceId}')
    return None

def find_device_hwinfo(hwInfoData, hwInstanceId):
    for hwInfo in hwInfoData:
        if hwInfo['hwInstanceId'] == hwInstanceId:
            return hwInfo
    logger(DEBUG, f'hwInfo not found for {hwInstanceId}')
    return None

def find_device_swinfo(swInfoData ,managedNeInstanceId):
    for swinfo in swInfoData:
        if swinfo['managedNeInstanceId'] == managedNeInstanceId:
            return swinfo
    logger(DEBUG, f'swInfo not found for {managedNeInstanceId}')
    return None

def find_field_bulletin(bulletinData, bulletinNumber):
    for bulletin in bulletinData:
        if bulletin['bulletinNumber'] == bulletinNumber:
            return bulletin
    logger(DEBUG, f'field bulletin not found for {bulletinNumber}')
    return None

def find_device_bulletin(bulletinData, securityAdvisoryInstanceId):
    for bulletin in bulletinData:
        if bulletin['securityAdvisoryInstanceId'] == securityAdvisoryInstanceId:
            return bulletin
    logger(DEBUG, f'sec bulletin not found for {securityAdvisoryInstanceId}')
    return None

###
#
# EOE Date
#	Indicates the End-of-Engineering (EOE) Date, if reached, otherwise the date is blank.
# EoExAnnouncement
#	Indicates the End-of-Life Announcement Date, which is the date the document announces
#	the end of sale, and end of life of a product that is distributed to the general public.
# EOL Date
#	Indicates the End-of-Life (EOL) Date, if reached, otherwise the date is blank. This is
#	the date the document announces the end of sale, and the end of life of a product is
#	distributed to the general public.
# EoLDoS Date
#	Indicates the End-of-Last Date of Support for the device, which is the last date to
#	receive service and support for the product. After this date, all support services for
#	the product are unavailable, and the product becomes obsolete.
# EoNSA Date
#	Indicates the End of New Service Attachment Date, for equipment and software that is
#	not covered by a service-and-support contract. This is the last date you can order a
#	new service-and-support contract or add the equipment and/or software to an existing#
#	service-and-support contract.
# EoRFA Date
#	Indicates End of Routine Failure Analysis Date, which is the last-possible date a routine
#	failure analysis may be performed to determine the cause of product failure or defect.
# EOS Date
#	Indicates the End-of-Service (EOS) Date, if reached, otherwise the date is blank. This is
#	the last date to order the product through Cisco point-of-sale mechanisms. The product is
#	no longer for sale after this date.
# EoSale Date
#	Indicates the End-of-Sale Date, which is the last date to order the product through Cisco
#	point-of-sale mechanisms. The product is no longer for sale after this date.
# EoSCR Date
#	Indicates the End of Service Contract Renewal (EoSCR). This the last date to extend or
#	renew a service contract for the product. The extension or renewal period may not extend
#	beyond the last date of support.
# EoSWM Date
#	Indicates the End of Software Maintenance Date, which is the last date that Cisco
#	Engineering may release any final software maintenance releases or bug fixes. After this
#	date, Cisco Engineering will no longer develop, repair, maintain, or test the product
#	software
def init_swServiceData(pcx, neInstanceId):
    for eol in swEOLData:
        if eol['neInstanceId'] == neInstanceId:
            # EoSWM -> EoSCR -> END_OF_SECURITY_VUL_SUPPORT_DATE -> LDoS
            if eol['currentSwEolMilestone'] == 'EoL':
                pcx['endOfLifeAnnounced']	= eol['currentSwEolMilestoneDate']
            if eol['currentSwEolMilestone'] == 'EoSale':
                pcx['endOfSale']		= eol['currentSwEolMilestoneDate']
            if eol['currentSwEolMilestone'] == 'EoSWM':
                pcx['lastShip']			= eol['currentSwEolMilestoneDate']
            if eol['currentSwEolMilestone'] == 'EoSWM':
                pcx['endOfSoftwareMaintenance']	= eol['currentSwEolMilestoneDate']
            if eol['currentSwEolMilestone'] == 'END_OF_SECURITY_VUL_SUPPORT_DATE':
                pcx['endOfVulnerabilitySecuritySupport'] = eol['currentSwEolMilestoneDate']
            if eol['currentSwEolMilestone'] == 'LDoS':
                pcx['ldosDate']	= eol['currentSwEolMilestoneDate']
        # end if
    #end for
    return pcx

def init_hwServiceData(pcx, hwInstanceId):
    for eol in hwEOLData:
        # EoLDoS -> EoSale->EoRFA->EoSCR->EoSWM->EoExAnnouncement->EoNSA
        if eol['hwInstanceId'] == hwInstanceId:
            if eol['currentHwEolMilestone'] == 'EoExAnnouncement':
                pcx['endOfLifeAnnounced']	= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'EoL':
                pcx['lastShip']			= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'EoNSA':
                pcx['endOfNewServiceAttach']	= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'EoRFA':
                pcx['endOfRoutineFailureAnalysis']= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'EoSCR':
                pcx['endOfServiceContractRenewal']= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'LDoS':
                pcx['ldosDate']			= eol['currentHwEolMilestoneDate']
            if eol['currentHwEolMilestone'] == 'EoSale':
                pcx['endOfSale']		= eol['currentHwEolMilestoneDate']
        #end if
    #end for

    # dont have these, blank them out
    pcx['contractNumber ']		= ""
    pcx['coverageStatus']		= ""
    pcx['coverageEndDate']		= ""
    pcx['coverageStartDate']		= ""

    return pcx

######################################################################
################## Start of functions to process customers ###########
######################################################################
#
# Wrapper function to loop over all customer
def process_allCustomers(partner, func, writer, args):
    processed_ids = set()
    
    with open(pcx_csv_allCustomers, 'r') as customers:
        customerList = csv.DictReader(customers)
        for customer in customerList:
            customerId = str(customer['customerId'])
            customerName = customer['customerName']

            # skip dups
            if customerId not in processed_ids:
                processed_ids.add(customerId)
                filename = f'{sntc_dir}{partner}/{customerName}'
                if os.path.isdir(filename):
                    logger(DEBUG, f"Processing:{customerName}")
                    func(customer, writer, args)
                else:
                    logger(DEBUG, f"Skipping {customerName}: Folder does not exist")
        # end for
    # end with

# CSV Naming Convention: Customer.csv
# JSON Naming Convention: Customers_Page_{page}_of_{total}.json
def pcx_customers(partner):
    items = []
    customerTotal = 0
    logger(INFO, f"    Reading SNTC Customer List.........................", end="")

    # Load the customer file. Fields are:
    # customerId,customerName,
    # streetAddress1,streetAddress2,streetAddress3,streetAddress4,
    # city,state,country,zipCode, theaterCode
    sntc_csv_customers = (sntc_dir + partner + '/Customers.csv')
    pcx_json_customers = (json_output_dir + 'Customers_Page_1_of_1.json')
    with open(sntc_csv_customers, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            customer_id		= row["customerId"]
            customer_name	= row["customerName"]
            customerNameTemp	= customer_name.replace(',', ' ')
            customerName	= customerNameTemp.replace('  ', ' ')

            items.append({
                "customerName": customer_name,
                "customerId": customer_id,
                "customerGUName": "",
                "successTracks": customerSuccessTracks
            })
    logger(INFO, 'SNTC Data Processed')

    # 
    # created the items data - parse it into associatged CSV files..
    logger(INFO, f"    Processing All Customer List.......................", end="")
    with open(pcx_csv_allCustomers, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,customerGUName,successTrackId,successTrackAccess'
        writer = csv.writer(target, delimiter=' ', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())

        for item in items:
            customerNameTemp = str(item['customerName'].replace('"', ','))
            customerName = customerNameTemp.replace(',', ' ')
            customerGUName = item['customerGUName'].replace(',', ' ')

            customerId = str(item['customerId'])
            successTrack = item['successTracks']

            for successTrackId in successTrack:
                trackId = str(successTrackId['id'])
                trackAccess = str(successTrackId['access'])
                CSV_Data = f'{customerId},{customerName},{customerGUName},{trackId},{trackAccess}'
                writer.writerow(CSV_Data.split())
                customerTotal += 1
            # PSNTC never has success track data
            logger(DEBUG, f'Found Customer {customerName}')
    #
    # Save JSON data
    save_json_file(items, pcx_json_customers)
    logger(INFO, 'SNTC Data Processed')

    #
    # All_Customers created, now create customers.csv
    # Nothing to do here exceot create the empty file as there are not STs
    logger(INFO, f"    Processing Customer List...........................", end="")
    with open(pcx_csv_customers, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,successTrackAccess'
        writer = csv.writer(target, delimiter=',', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())
    #
    save_json_file(items, pcx_json_customers)
    logger(INFO, 'SNTC Data Processed')

    logger(INFO, f'    Total customers records {customerTotal}')
    logger(DEBUG, f'Total customers records {customerTotal}')
    
######################################################################
####### Start of functions to generate Success Track PCX data ########
######################################################################
# SNTC does not offer Success Track, but we create the static template anyway
#
# CSV Naming Convention: SuccessTracks.csv
# JSON Naming Convention: SuccessTracks.json
def pcx_successtracks(partner):
    tracks = []
    logger(INFO, f"    Processing Success Tracks Report...................", end="")
    
    # Write CSV file
    with open(pcx_csv_successTracks, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        CSV_Header = 'successTracksId,successTrackName,useCaseName,useCaseId'
        writer.writerow(CSV_Header.split(','))
    
        # Write the data - only unique use cases are added
        processed_ids = set()
        for useCaseRow in ciscoUseCases:
            useCaseId = useCaseRow[3]
            if useCaseId not in processed_ids:
                processed_ids.add(useCaseId)
                row = useCaseRow[:4]
                writer.writerow(row)
                tracks.append(row)
        # for

    # Save JSON version
    json_filename = (json_output_dir + 'SuccessTracks.json')
    save_json_file(tracks, json_filename)

    logger(INFO, 'SNTC Data Processed')

########################################################################
########## Start of functions to generate Lifecycle PCX data ###########
########################################################################
#
# SNTC does not offer Lifecycle data - save the blank files as needed
#
# CSV Naming Convention: Lifecycle.csv
# JSON Naming Convention: {Customer ID}_Lifecycle.json
def pcx_lifecycle_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']

    logger(INFO, f"    Processing Lifecycle Report for {customer['customerName']}..", end="" )
    for useCase in ciscoUseCases:
        row = [col for col in useCase]	# Copy existing columns
        row.insert(0, customerName)	# Add customer name to beginning
        row.append('FALSE')		# Add pitstop completed flag as FASLE
        writer.writerow(row)		# save to CSV
        items.append(row)		# and a copy for JSON

    for successTrackId in ciscoSuccessTracks:
        json_filename = (json_output_dir + str(customerId) + '_Lifecycle_' + successTrackId + '.json')
        save_json_file(items, json_filename)
    logger(INFO, 'SNTC Data Processed')

def pcx_lifecycle(partner):
    logger(DEBUG, '********************** Running Lifecycle Report **********************\n')

    CSV_Header = 'customerName,successTracksId,successTrackName,useCaseName,useCaseId,' \
        'currentPitstopName,pitStopName,pitstopActionName,pitstopActionId,pitstopActionCompleted'

    with open(pcx_csv_lifecycle, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())
        process_allCustomers(partner, pcx_lifecycle_worker, writer, None)
       
######################################################################
########## Start of functions to generate Partner PCX data ###########
######################################################################
#
# SNTC does not offer Partner_Offers data - save the blank files as needed
#	CSV - save the blank file
#	JSON - file not created
#
# CSV Naming Convention: Partner_Offers.csv
# JSON Naming Convention: Partner_Offers.json
def pcx_partner_offers(partner):
    logger(INFO, f"    Processing Partner Offers Report...................", end="")
    pcx_json_partnerOffers = (json_output_dir + 'Partner_Offers.json')
    CSV_Header = 'customerId,offerId,offerType,title,description,duration,accTimeRequiredHours,imageFileName,' \
        'customerRating,status,userFirstName,userLastName,userEmailId,createdBy,createdOn,' \
        'modifiedBy,modifiedOn,language,mappingId,successTrackId,successTrackName,usecaseId,usecase,' \
        'pitstopId,pitstop,mappingChecklistId,checklistId,checklist,publishedToAllCustomers,' \
        'customerEntryId,companyName'

    with open(pcx_csv_partnerOffers, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())

    logger(INFO, 'SNTC Data Not Available')

# SNTC does not offer Partner_Offer Sessions data -
#	CSV - save the blank file
#	JSON - file not created
#
# CSV Naming Convention: Partner_Offer_Sessions.csv
# JSON Naming Convention: Partner_Offer_Sessions.json
def pcx_partner_offer_sessions(partner):
    logger(INFO, f"    Processing Partner Offers Sessions Report..........", end="")

    with open(pcx_csv_partnerOfferSessions, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,companyName,offerId,sessionId,timezone,status,attendeeId,ccoId,' \
            'attendeeUserEmail,attendeeUserFullName,noOfAttendees,preferredSlot,businessOutcome,' \
            'reasonForInterest,createdDate,modifiedDate'
        writer = csv.writer(target, delimiter=' ', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())

    logger(INFO, 'SNTC Data Not Available')

def pcx_all_offers(partner):
    pcx_partner_offers(partner)
    pcx_partner_offer_sessions(partner)

#####################################################################
######### Start of functions to generate Contract PCX data ##########
###### SNTC does not have contracts so all these will be empty ######
#####################################################################
def pcx_contracts(partner):
    logger(INFO, f"    Processing Contracts Report........................", end="")

    with open(pcx_csv_contracts, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerName,contractNumber,cuid,cavid,contractStatus,contractValue,currency,serviceLevel,' \
            'startDate,endDate,currencySymbol,onboardedstatus'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_contracts_details(partner):
    logger(INFO, f"    Processing Contracts Details Report................", end="")

    with open(pcx_csv_contractsDetails, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerName,customerGUName,customerHQName,contractNumber,productId,serialNumber,' \
            'contractStatus,componentType,serviceLevel,coverageStartDate,coverageEndDate,' \
            'installationQuantity,instanceNumber'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_contractswithcustomernames(partner):
    logger(INFO, f"    Processing Contract With Customer Names Report.....", end="")

    with open(pcx_csv_contractsWithCustomers, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerName,customerId,contractNumber,contractStatus,contractValue,customerGUName,' \
            'successTrackId,serviceLevel,coverageStartDate,coverageEndDate,onboardedstatus'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_contractsL2(partner):
    logger(INFO, f"    Processing L2 Contracts Report.....................", end="")

    with open(pcx_csv_contractsL2, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,serviceLevel,successTrackAccess'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))
        
    logger(INFO, 'SNTC Data Not Available')
    return
#
# SNTC does not have contracts so all these will be empty
#	Contracts.csv
#	Contract_Details.csv
#	Contracts_With_Customer_Names.csv
#	L2_contracts.csv
def pcx_all_contracts(partner):
    pcx_contracts(partner)
    pcx_contracts_details(partner)
    pcx_contractswithcustomernames(partner)
    pcx_contractsL2(partner)

#####################################################################
####### Start of functions to generate Asset Related PCX data #######
#####################################################################
#
# CSV Naming Convention: Assets.csv
# JSON Naming Convention: {Customer ID}_Assets_{UniqueReportID}.json
def pcx_reports_assets_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing Assets Report...........................", end="")

    UniqueReportID = 0

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Security_Advisories.csv'
    sec_advisories = read_csv_dict(filename)

    for asset in assetData:
        # Initialize pcx with all keys set to empty strings
        pcx = init_pcxData(CSV_Header, customerId)

        pcx['assetId']			= asset['neInstanceId']
        pcx['assetName']		= asset['hostname']
        pcx['ipAddress']		= asset['ipAddress']

        pcx['productDescription']	= asset['sysDescr']
        pcx['productFamily']		= asset['productFamily']
        pcx['productType']		= asset['productType']
        pcx['productId']		= asset['productId']

        pcx['role']			= ""
        pcx['connectionStatus']		= asset['reachabilityStatus']
        pcx['lastScan']			= asset['inventoryCollectionDate']
        pcx['location']			= asset['sysLocation']
        pcx['managedBy']		= asset['managementAddress']

        if asset['swType']:
            # Fill in what software info we have
            pcx['assetType']	= "Software"
            pcx['softwareType']		= asset['swType']
            pcx['softwareRelease']	= asset['swVersion']

            init_swServiceData(pcx, asset['neInstanceId'])

        else:
            # Fill in what hardware info we have
            pcx['assetType']	= "Hardware"
            hwinfo = find_device_by_neId(hwInfoData, asset['neInstanceId'])
            if hwinfo:
                pcx['serialNumber']	= hwinfo['serialNumber']
                pcx['softwareRelease']	= hwinfo['swVersion']

                # Find number of advisories for this asset
                pcx['criticalSecurityAdvisories']	= find_device_security_cnt(sec_advisories, hwinfo['hwInstanceId'])
                pcx['advisories']			= find_device_advisory_cnt(asset['neInstanceId'])

            else:
                logger(WARNING, f"hwinfo missing for neInstanceId:{asset['neInstanceId']}")
            init_hwServiceData(pcx, asset['neInstanceId'])
        # end if

        # SNTC Data Not Available
        pcx['profileName']		= ""
        pcx['addressLine1']		= ""
        pcx['addressLine2']		= ""
        pcx['addressLine3']		= ""
        
        pcx['hclStatus']		= ""
        pcx['ucsDomain']		= ""
        pcx['hxCluster']		= ""

        pcx['licenseStatus']		= ""
        pcx['licenseLevel']		= ""
        pcx['subscriptionId']		= ""
        pcx['subscriptionStartDate']	= ""
        pcx['subscriptionEndDate']	= ""

        pcx['supportType']		= ""
        pcx['coverageStatus']		= "UNKNOWN"

        writer.writerow([pcx[key] for key in CSV_Header.split(',')])
        items.append(pcx)		# and a copy for JSON
    #end for

    # now save the data to the JSON file
    json_filename = (json_output_dir + str(customerId) + '_Assets_' + str(UniqueReportID) + '.json')
    save_json_file(items, json_filename)

    logger(INFO, 'SNTC Data Processed')
    return

# CSV Naming Convention: Hardware.csv
# JSON Naming Convention: {Customer ID}_Hardware_{UniqueReportID}.json
def pcx_reports_hardware_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing Hardware Report.........................", end="")

    UniqueReportID = 0

    for hwinfo in hwInfoData:
        # Initialize pcx with all keys set to empty strings
        pcx = init_pcxData(CSV_Header, customerId)

        pcx['productId']		= hwinfo['productId']
        pcx['serialNumber']		= hwinfo['collectedSerialNumber']
        pcx['hwInstanceId']		= hwinfo['hwInstanceId']

        asset = find_device_by_neId(assetData, hwinfo['managedNeInstanceId'])
        if asset:
            pcx['assetId']		= asset['neInstanceId']
            pcx['assetName']	= asset['hostname']
            pcx['productFamily']	= ""
        else:
            logger(WARNING, f"asset missing for advisory['managedNeInstanceId']")

        init_hwServiceData(pcx, hwinfo['hwInstanceId'])
        writer.writerow([pcx[key] for key in CSV_Header.split(',')])
        items.append(pcx)		# and a copy for JSON

    #end for

    # now save the data to the JSON file
    json_filename = (json_output_dir + str(customerId) + '_Hardware_' + str(UniqueReportID) + '.json')
    save_json_file(items, json_filename)

    logger(INFO, 'SNTC Data Processed')
    return

# CSV Naming Convention: Software.csv
# JSON Naming Convention: {Customer ID}_Software_{UniqueReportID}.json
def pcx_reports_software_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing Software Report.........................", end="")

    UniqueReportID = 0

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Software_Bulletins.csv'
    bulletins = read_csv_dict(filename)

    # customerId,successTrackId,useCaseId,
    # assetName,assetId,productId,
    # softwareType softwareRelease
    # endOfLifeAnnounced,endOfSoftwareMaintenance,endOfSale,lastShip,endOfVulnerabilitySecuritySupport,ldosDate

    for swinfo in swInfoData:
        # Initialize pcx with all keys set to empty strings
        pcx = init_pcxData(CSV_Header, customerId)

        pcx['softwareType']		= swinfo['swType']
        pcx['softwareRelease']		= swinfo['swVersion']

        asset = find_device_by_neId(assetData, swinfo['managedNeInstanceId'])
        if asset:
            pcx['assetName']		= asset['hostname']
            pcx['assetId']		= asset['neInstanceId']
            pcx['productId']		= asset['productId']
        else:
            logger(WARNING, f"Asset missing for swinfo['managedNeInstanceId']")

        if bulletins:
            for bulletin in bulletins:
                if swinfo['swType'] == bulletin['swType'] and \
                   swinfo['swMajorVersion'] == bulletin['swMajorVersion']:
                 pcx['endOfLifeAnnounced']		  = bulletin['eoLifeAnnouncementDate']
                 pcx['endOfSoftwareMaintenance']	  = bulletin['eoSwMaintenanceReleasesDate']
                 pcx['endOfSale']			  = bulletin['eoSaleDate']
                 pcx['lastShip']			  = ''
                 pcx['endOfVulnerabilitySecuritySupport'] = bulletin['eoVulnerabilitySecuritySupport']
                 pcx['ldosDate']			  = bulletin['lastDateOfSupport']
                 break
        else:
            init_swServiceData(pcx, swinfo['managedNeInstanceId'])
            logger(WARNING, f"Bulletin missing for managedNeInstanceId:{swinfo['managedNeInstanceId']} :: {swinfo['swType']} :: {swinfo['swVersion']}")
            
        writer.writerow([pcx[key] for key in CSV_Header.split(',')])
        items.append(pcx)		# and a copy for JSON

    #end for

    # now save the data to the JSON file
    json_filename = (json_output_dir + str(customerId) + '_Software_' + str(UniqueReportID) + '.json')
    save_json_file(items, json_filename)

    logger(INFO, 'SNTC Data Processed')
    return

def pcx_reports_licenses_worker(customer, writer, CSV_Header):
    logger(INFO, f"    Processing License Report..........................", end="")
    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_reports_licenses_purchased_worker(customer, writer, CSV_Header):
    logger(INFO, f"    Processing License Purchased Report................", end="")
    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_reports_priority_bugs_worker(customer, writer, CSV_Header):
    logger(INFO, f"    Processing Priority Bugs Report....................", end="")
    logger(INFO, 'SNTC Data Not Available')
    return

# CSV Naming Convention: Field_Notices.csv
# JSON Naming Convention: {Customer ID}_Field_Notices_{UniqueReportID}.json
def pcx_reports_field_notices_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing Field Notices Report....................", end="")

    UniqueReportID = 0

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Field_Notices.csv'
    notices = read_csv_dict(filename)

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Feild_Notice_Bulletins.csv'
    bulletins = read_csv_dict(filename)

    if notices:
        for notice in notices:
            # Initialize pcx with all keys set to empty strings
            pcx = init_pcxData(CSV_Header, customerId)

            asset = find_device_by_neId(assetData, notice['neInstanceId'])
            hwinfo = find_device_by_neId(hwInfoData, notice['neInstanceId'])
            bulletin = find_field_bulletin(bulletins, notice['bulletinNumber'])

            pcx['customerId']			= customerId
            pcx['successTrackId']		= ""
            pcx['useCaseId']			= ""
            pcx['hwInstanceId']			= notice['hwInstanceId']
            pcx['fieldNoticeId']		= notice['bulletinNumber']
            pcx['affectedStatus']		= notice['vulnerabilityStatus']
            pcx['affectedReason']		= notice['vulnerabilityReason']

            if asset:
                pcx['assetName']		= asset['hostname']
                pcx['assetId']			= asset['neInstanceId']
                pcx['productId']		= asset['productId']
                pcx['ipAddress']		= asset['ipAddress']
            else:
                logger(WARNING, f"asset missing for {notice['neInstanceId']}")

            if hwinfo:
                pcx['serialNumber']		= hwinfo['serialNumber']
                pcx['softwareRelease']		= hwinfo['swVersion']
            else:
                logger(WARNING, f"hwinfot missing for {notice['neInstanceId']}")

            if bulletin:
                pcx['updated']			= bulletin['bulletinLastUpdated']
                pcx['title']			= bulletin['bulletinTitle']
                pcx['created']			= bulletin['bulletinFirstPublished']
                pcx['fieldNoticeDescription']	= bulletin['bulletinSummary']
                pcx['url']			= bulletin['url']
                pcx['additionalNotes']		= ""

            writer.writerow([pcx[key] for key in CSV_Header.split(',')])
            items.append(pcx)		# and a copy for JSON
        # end for

        # Save JSON data
        json_filename = (json_output_dir + str(customerId) + '_Field_Notices__' + str(UniqueReportID) + '.json')
        save_json_file(items, json_filename)
        logger(INFO, 'SNTC Data Processed')
    else:
        logger(INFO, 'No Notices Found')
    # end if

    return

# Hardware Security Advisories
#
# CSV Naming Convention: Security_Advisories.csv
# JSON Naming Convention: {Customer ID}_SecurityAdvisories_{UniqueReportID}.json
def pcx_reports_security_advisories_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing Security Advisories Report..............", end="")

    UniqueReportID = 0
        
    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Security_Advisories.csv'
    advisories = read_csv_dict(filename)

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Security_Advisory_Bulletins.csv'
    bulletins = read_csv_dict(filename)

    if advisories:
        for advisory in advisories:
            # Initialize pcx with all keys set to empty strings
            pcx = init_pcxData(CSV_Header, customerId)

            pcx['affectedStatus']	= advisory['vulnerabilityStatus']
            pcx['affectedReason']	= advisory['vulnerabilityReason']
           
            asset = find_device_by_neId(assetData, advisory['neInstanceId'])
            if asset:
                pcx['assetName']	= asset['hostname']
                pcx['assetId']		= asset['neInstanceId']
                pcx['productId']	= asset['productId']
                pcx['ipAddress']	= asset['ipAddress']
                pcx['softwareRelease']	= asset['swVersion']
            else:
                logger(WARNING, f"asset missing for advisory['neInstanceId']")

            hwinfo = find_device_hwinfo(hwInfoData, advisory['hwInstanceId'])
            if hwinfo:
                pcx['serialNumber']		= hwinfo['collectedSerialNumber']
            else:
                logger(WARNING, f"hwinfo missing for advisory['hwInstanceId']")

            bulletin = find_device_bulletin(bulletins, advisory['securityAdvisoryInstanceId'])
            if bulletin:
                pcx['advisoryId']	= bulletin['advisoryId']
                pcx['impact']		= bulletin['securityImpactRating']
                pcx['cvss']		= bulletin['cvssBaseScore']
                pcx['version']		= bulletin['bulletinVersion']
                pcx['cve']		= bulletin['cveId']
                pcx['published']	= bulletin['bulletinFirstPublished']
                pcx['updated']		= bulletin['bulletinLastUpdated']
                pcx['advisory']		= bulletin['bulletinTitle']
                pcx['summary']		= bulletin['bulletinSummary']
                pcx['url']		= bulletin['url']
                pcx['additionalNotes']	= bulletin['ciscoBugIds']
                pcx['additionalVerificationNeeded'] = bulletin['alertAutomationCaveat']
            else:
                logger(WARNING, f"bulletin missing for advisory['securityAdvisoryInstanceId']")

            writer.writerow([pcx[key] for key in CSV_Header.split(',')])
            items.append(pcx)		# and a copy for JSON
        # end for

        # now save the data to the JSON file
        json_filename = (json_output_dir + str(customerId) + '_SecurityAdvisories_' + str(UniqueReportID) + '.json')
        save_json_file(items, json_filename)

        logger(INFO, 'SNTC Data Processed')
    else:
        logger(INFO, 'No Advisories Found')
    # end if

    return


def pcx_device_reports_lic_worker(customer, writer, items):
    CSV_Header = 'customerId,successTrackId,useCaseId,assetName,assetId,productFamily,productType,' \
        'connectionStatus,productDescription,licenseId,licenseStartDate,licenseEndDate,' \
        'contractNumber,subscriptionId,supportType'
    mode = 'a' if os.path.exists(pcx_csv_licenses) else 'w'
    with open(pcx_csv_licenses, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_licenses_worker(customer, writer, CSV_Header)


    CSV_Header = 'customerId,successTrackId,useCaseId,licenseId,licenseLevel,purchasedQuantity,' \
        'productFamily,licenseStartDate,licenseEndDate,contractNumber'
    mode = 'a' if os.path.exists(pcx_csv_purchasedLicenses) else 'w'
    with open(pcx_csv_purchasedLicenses, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_licenses_purchased_worker(customer, writer, CSV_Header)

    CSV_Header = 'customerId,successTrackId,useCaseId,assetName,assetId,serialNumber,ipAddress,' \
        'softwareRelease,productId,bugId,bugTitle,description,url,bugSeverity,impact'
    mode = 'a' if os.path.exists(pcx_csv_priorityBugs) else 'w'
    with open(pcx_csv_priorityBugs, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_priority_bugs_worker(customer, writer, CSV_Header)

def pcx_all_device_lic_reports(partner):
    process_allCustomers(partner, pcx_device_reports_lic_worker, None, None)


def pcx_device_reports_worker(customer, writer, items):
    global assetData
    global hwInfoData
    global swInfoData
    global hwEOLData
    global swEOLData

    logger(INFO, f"  Processing Assets Report for {customer['customerName']}")

    # load all the devices data for this customer
    assetData = read_device_assets(customer, partner)
    hwInfoData = read_device_hwInfo(customer, partner)
    swInfoData = read_device_swInfo(customer, partner)
    hwEOLData = read_device_hwEOLInfo(customer, partner)
    swEOLData = read_device_swEOLInfo(customer, partner)

    missing = [name for data, name in [
        (assetData, 'assetData'),
        (hwInfoData, 'hwInfoData'),
        (swInfoData, 'swInfoData')
    ] if not data]

    if missing:
        logger(INFO, f"    Skipping...........................................{', '.join(missing)} Not Available")
        return
        
    # OK, devices all populated, lets create the PCX files from the data
    #
    CSV_Header = 'customerId,successTrackId,useCaseId,' \
        'assetId,assetName,productFamily,productType,' \
        'serialNumber,productId,ipAddress,productDescription,softwareType,softwareRelease,role,' \
        'location,coverageStatus,lastScan,endOfLifeAnnounced,endOfSale,lastShip,' \
        'endOfRoutineFailureAnalysis,endOfNewServiceAttach,endOfServiceContractRenewal,ldosDate,' \
        'connectionStatus,managedBy,contractNumber,coverageEndDate,coverageStartDate,supportType,' \
        'advisories,assetType,criticalSecurityAdvisories,addressLine1,addressLine2,addressLine3,' \
        'licenseStatus,licenseLevel,profileName,hclStatus,ucsDomain,hxCluster,subscriptionId,' \
        'subscriptionStartDate,subscriptionEndDate'
    mode = 'a' if os.path.exists(pcx_csv_assets) else 'w'
    with open(pcx_csv_assets, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_assets_worker(customer, writer, CSV_Header)

    CSV_Header = 'customerId,successTrackId,useCaseId,assetName,assetId,hwInstanceId,productId,serialNumber,' \
        'fieldNoticeId,updated,title,created,url,additionalNotes,affectedStatus,affectedReason,' \
        'fieldNoticeDescription,softwareRelease,ipAddress'
    mode = 'a' if os.path.exists(pcx_csv_fieldNotices) else 'w'
    with open(pcx_csv_fieldNotices, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_field_notices_worker(customer, writer, CSV_Header)


    CSV_Header = 'customerId,successTrackId,useCaseId,assetName,assetId,ipAddress,serialNumber,advisoryId,' \
        'impact,cvss,version,cve,published,updated,advisory,summary,url,additionalNotes,' \
        'affectedStatus,affectedReason,additionalVerificationNeeded,softwareRelease,productId'
    mode = 'a' if os.path.exists(pcx_csv_SWGroupSuggestionsAdvisories) else 'w'
    with open(pcx_csv_SWGroupSuggestionsAdvisories, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_security_advisories_worker(customer, writer, CSV_Header)


    CSV_Header = 'customerId,successTrackId,useCaseId,assetId,hwInstanceId,assetName,productFamily,productId,' \
        'serialNumber,endOfLifeAnnounced,endOfSale,lastShip,endOfRoutineFailureAnalysis,' \
        'endOfNewServiceAttach,endOfServiceContractRenewal,ldosDate,coverageEndDate,' \
        'coverageStartDate,contractNumber,coverageStatus'
    mode = 'a' if os.path.exists(pcx_csv_hardware) else 'w'
    with open(pcx_csv_hardware, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_hardware_worker(customer, writer, CSV_Header)

    
    CSV_Header = 'customerId,successTrackId,useCaseId,assetName,assetId,productId,softwareType,' \
        'softwareRelease,endOfLifeAnnounced,endOfSoftwareMaintenance,endOfSale,lastShip,' \
        'endOfVulnerabilitySecuritySupport,ldosDate'
    mode = 'a' if os.path.exists(pcx_csv_software) else 'w'
    with open(pcx_csv_software, mode, encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(CSV_Header.split(','))
        pcx_reports_software_worker(customer, writer, CSV_Header)




def pcx_all_device_reports(partner):
    process_allCustomers(partner, pcx_device_reports_worker, None, None)

######################################################################
#### Start of functions to generate Compliance Related PCX data ######
######################################################################
#
# CSV Naming Convention: Regulatory_Compliance_Obtained.csv
# JSON Naming Convention: {Customer ID}_Obtained_{successTrackId}.json
def pcx_compliance_optin_worker(customer, writer, CSV_Header):
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    status = "Customer has not opted for Compliance. Please work with the customer get the Compliance reports enabled.",
    access = "FALSE"

    logger(INFO, f"    Processing Compliance OptIn for customer {customerName}..", end="" )
    for successTrackId in ciscoSuccessTracks:
        row = [customerId, customerName, successTrackId, status, access]
        writer.writerow(row)
        items.append(row)		# and a copy for JSON

    for successTrackId in ciscoSuccessTracks:
        json_filename =  (json_output_dir + str(customerId) + '_Obtained_' + successTrackId + '.json')
        save_json_file(items, json_filename)

    logger(INFO, 'SNTC Data Processed')
        
def pcx_compliance_optin(partner):
    CSV_Header = 'customerId,customerName,successTracksId,status,hasQualifiedAssets'

    with open(pcx_csv_RCCObtained, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=' ', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split())
        process_allCustomers(partner, pcx_compliance_optin_worker, writer, None)

def pcx_compliance_violations(partner):
    logger(INFO, f"    Processing Compliance Violation Reports ...........", end="" )
    with open(pcx_csv_RCCComplianceViolations, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,severity,severityId,policyGroupId,policyGroupName,' \
            'policyId,ruleId,policyName,ruleTitle,violationCount,affectedAssetsCount,swType,policyCategory'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_compliance_assets_violating_rule(partner): 
    logger(INFO, f"    Processing Compliance Asset Violation Rule Reports.", end="" )
    with open(pcx_csv_RCCAssetsViolatingComplianceRule, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,mgmtSystemHostname,mgmtSystemType,ipAddress,' \
            'productFamily,violationCount,role,assetId,assetName,softwareType,softwareRelease,productId,' \
            'severity,lastChecked,policyId,ruleId,scanStatus'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_compliance_rule_details(partner):
    logger(INFO, f"    Processing Compliance Rule Detail Reports..........", end="" )
    with open(pcx_csv_RCCPolicyRuleDetails, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,policyName,policyDescription,ruleId,policyId'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_compliance_suggestions(partner):
    logger(INFO, f"    Processing Compliance Suggestion Reports ..........", end="" )
    with open(pcx_csv_RCCComplianceSuggestions, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,policyId,policyCategory,policyGroupId,ruleId,' \
            'severity,violationMessage,suggestion,affectedAssetsCount'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_compliance_assets_violations(partner):
    logger(INFO, f"    Processing Compliance Asset Violation Reports .....", end="" )
    with open(pcx_csv_RCCAssetViolations, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,sourceSystemId,assetId,successTrackId,severity,regulatoryType,' \
            'violationMessage,suggestion,violationAge,policyDescription,ruleTitle,ruleDescription'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_compliance_assets_with_violations(partner):
    logger(INFO, f"    Processing Compliance Asset With Violations Reports", end="" )
    with open(pcx_csv_RCCAssetsWithViolations, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,ipAddress,serialNumber,violationCount,assetGroup,' \
            'role,sourceSystemId,assetId,assetName,lastChecked,softwareType,softwareRelease,severity,' \
            'severityId,policyId,ruleId,scanStatus'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

#
# SNTC does not offer Compliance data - save the blank files as needed
def pcx_all_compliance_reports(partner):
    pcx_compliance_violations(partner)
    pcx_compliance_rule_details(partner)
    pcx_compliance_suggestions(partner)
    pcx_compliance_assets_violations
    pcx_compliance_assets_with_violations
    pcx_compliance_assets_violating_rule

######################################################################
##### Start of functions to generate Software Related PCX data #######
######################################################################
#
def pcx_software_groups(partner):
    logger(INFO, f"    Processing Software Group Reports .................", end="") 
    with open(pcx_csv_SWGroups, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,suggestionId,riskLevel,softwareGroupName,sourceId,' \
            'productFamily,softwareType,currentReleases,selectedRelease,assetCount,suggestions,' \
            'sourceSystemId,softwareGroupId,managedBy'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_software_group_suggestions(partner):
    logger(INFO, f"    Processing SWG Suggestion Reports .................", end="") 
    with open(pcx_csv_SWGroupSuggestionsTrend, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,suggestionId,suggestionsInterval,' \
            'suggestionUpdatedDate,suggestionSelectedDate,changeFromPrev,riskCategory,riskDate,' \
            'riskScore'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))
    with open(pcx_csv_SWGroupSuggestionsReleases, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,suggestionId,suggestionsInterval,' \
            'suggestionUpdatedDate,suggestionSelectedDate,releaseSummaryName,releaseSummaryReleaseDate,' \
            'releaseSummaryRelease'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))
    with open(pcx_csv_SWGroupSuggestionSummaries, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,suggestionId,suggestionsInterval,' \
            'suggestionUpdatedDate,suggestionSelectedDate,machineSuggestionId,expectedSoftwareGroupRisk,' \
            'expectedSoftwareGroupRiskCategory,name,releaseDate,release,releaseNotesUrl,' \
            'fieldNoticeSeverityFixedHigh,fieldNoticeSeverityFixedMedium,fieldNoticeSeverityFixedLow,' \
            'fieldNoticeSeverityNewExposedHigh,fieldNoticeSeverityNewExposedMedium,' \
            'fieldNoticeSeverityNewExposedLow,fieldNoticeSeverityExposedHigh,' \
            'fieldNoticeSeverityExposedMedium,fieldNoticeSeverityExposedLow,advisoriesSeverityFixedHigh,' \
            'advisoriesSeverityFixedMedium,advisoriesSeverityFixedLow,advisoriesSeverityNewExposedHigh,' \
            'advisoriesSeverityNewExposedMedium,advisoriesSeverityNewExposedLow,' \
            'advisoriesSeverityExposedHigh,advisoriesSeverityExposedMedium,advisoriesSeverityExposedLow,' \
            'bugSeverityFixedHigh,bugSeverityFixedMedium,bugSeverityFixedLow,bugSeverityNewExposedHigh,' \
            'bugSeverityNewExposedMedium,bugSeverityNewExposedLow,bugSeverityExposedHigh,' \
            'bugSeverityExposedMedium,bugSeverityExposedLow,featuresCountActiveFeaturesCount,' \
            'featuresCountAffectedFeaturesCount,featuresCountFixedFeaturesCount'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return 

def pcx_software_group_assets(partner):
    logger(INFO, f"    Processing SWG Assets Reports .....................", end="") 
    with open(pcx_csv_SWGroupSuggestionAssets, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,softwareGroupId,deploymentStatus,selectedRelease,' \
            'assetName,ipAddress,softwareType,currentRelease'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
   
def pcx_software_group_bug_list(partner):
    logger(INFO, f"    Processing SWG Bug Reports ........................", end="") 
    with open(pcx_csv_SWGroupSuggestionsBugList, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,machineSuggestionId,bugId,severity,title,state,' \
            'affectedAssets,features'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return


def pcx_swg_field_notice_worker(customer, writer, CSV_Header):
    machine_data = {}
    items = []
    customerId = str(customer['customerId'])
    customerName = customer['customerName']
    logger(INFO, f"    Processing SWG Field Notice for {customer['customerName']}..", end="" )

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Field_Notices.csv'
    notices = read_csv_dict(filename)

    filename = f'{sntc_dir}/{partner}/{customerName}/csv/{customerId}_Feild_Notice_Bulletins.csv'
    bulletins = read_csv_dict(filename)

    if bulletins:
        for bulletin in bulletins:
            if bulletin['fieldNoticeType'] == "Software":
                # Initialize pcx with all keys set to empty strings
                pcx = init_pcxData(CSV_Header, customerId)
                found = False
                pcx['customerId']		= customerId
                pcx['customerName']		= customerName
                pcx['successTrackId']		= ""
                pcx['fieldNoticeId']		= bulletin['bulletinNumber']
                pcx['title']			= bulletin['bulletinTitle']
                pcx['state']			= ""
                pcx['firstPublished']		= bulletin['bulletinFirstPublished']
                pcx['lastUpdated'] 		= bulletin['bulletinLastUpdated']

                if notices:
                    for notice in notices:
                        if notice['bulletinNumber'] == bulletin['bulletinNumber']:
                            found = True
                            pcx['machineSuggestionId']	= notice['hwInstanceId']
                            writer.writerow([pcx[key] for key in CSV_Header.split(',')])
                            items.append(pcx)		# and a copy for JSON
                        #end if
                    #end for
                #end if

                if found == False:
                    pcx['machineSuggestionId']	= "0"
                    writer.writerow([pcx[key] for key in CSV_Header.split(',')])
                    logger(WARNING, f"No notice found for bulletinNumber:{bulletin['bulletinNumber']}")
                #end if
            # end if
        # end for
    # end if

    # Organize items by machineId
    for item in items:
        machineSuggestionId = item['machineSuggestionId']
        if machineSuggestionId not in machine_data:
            machine_data[machineSuggestionId] = []
        machine_data[machineSuggestionId].append(item)
    
    # Save each machine's data to a separate JSON file
    for machineSuggestionId, data in machine_data.items():
        json_filename = (json_output_dir + str(customerId) +
                         '_SoftwareGroup_Suggestions_Field_Notices_' +
                         str(machineSuggestionId) + '_Page_1_of_1.json')
        save_json_file(data, json_filename)
    # end for
    logger(INFO, 'SNTC Data Processed') if bulletins else logger(INFO, 'No Field Notices Found')

# CSV Naming Convention: SoftwareGroup_Suggestions_Field_Notices.csv
# JSON Naming Convention: {Customer ID}_SoftwareGroup_Suggestions_Field_Notices_{Machine Suggestion ID}_Page_{page}_of_{total}.json
def pcx_software_group_field_notices(partner):
    with open(pcx_csv_SWGroupSuggestionsFieldNotices, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,machineSuggestionId,fieldNoticeId,title,state,' \
            'firstPublished,lastUpdated'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))
        process_allCustomers(partner, pcx_swg_field_notice_worker, writer, CSV_Header)
    # end while
    return

# Software Security Advisories
#
# CSV Naming Convention: SoftwareGroup_Suggestions_Security_Advisories.csv
# JSON Naming Convention: {Customer ID}_SoftwareGroup_Suggestions_Security_Advisories_{Machine Suggestion ID}_Page_{page}_of_{total}.json
def pcx_software_group_advisories(partner):

    logger(INFO, f"    Processing SWG Security Advisories ................", end="")

    CSV_Header = 'customerId,customerName,successTrackId,machineSuggestionId,state,advisoryId,impact,title,' \
        'updated,advisoryVersion'

    with open(pcx_csv_SWGroupSuggestionsAdvisories, 'w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')

def pcx_all_software_reports(partner):
    pcx_software_groups(partner)

def pcx_all_software_groups(partner):
    pcx_software_group_field_notices(partner)
    pcx_software_group_suggestions(partner)
    pcx_software_group_assets(partner)
    pcx_software_group_advisories(partner)
    pcx_software_group_bug_list(partner)

######################################################################
# Start of functions to generate Automated Fault Management PCX data #
######################################################################
#
def pcx_afm_faults(partner):
    logger(INFO, f"    Processing AFM Fault Reports ......................", end="")
    with open(pcx_csv_AFMFaults, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,severity,title,lastOccurence,condition,' \
            'caseAutomation,faultId,category,openCases,affectedAssets,occurences,ignoredAssets,' \
            'mgmtSystemType,mgmtSystemAddr,mgmtSystemHostName'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_afm_fault_summary(partner):
    logger(INFO, f"    Processing AFM Fault Summary Reports ..............", end="")
    with open(pcx_csv_AFMFaultSummary, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,faultId,suggestion,impact,description,severity,' \
            'title,condition,category,supportedProductSeries'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_afm_affected_assets(partner):
    logger(INFO, f"    Processing AFM Affected Assets Reports ............", end="")
    with open(pcx_csv_AFMFaultAffectedAssets, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,faultId,assetName,productId,caseNumber,caseAction,' \
            'occurrences,firstOccurrence,lastOccurrence,serialNumber,mgmtSystemType,mgmtSystemAddr,' \
            'mgmtSystemHostName'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_afm_fault_history(partner):
    logger(INFO, f"    Processing AFM History Reports ................,,..", end="")
    with open(pcx_csv_AFMFaultHistory, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,faultId,assetName,status,failureMessage,lastOccurrence'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_all_afm_reports(partner):
    pcx_afm_faults(partner)
    pcx_afm_fault_summary(partner)
    pcx_afm_affected_assets(partner)
    pcx_afm_fault_history(partner)

######################################################################
# Start of functions to generate Automated Fault Management PCX data #
######################################################################
#
def pcx_crash_risk_assets(partner):
    logger(INFO, f"    Processing Crash Risk Reports .....................", end="")
    with open(pcx_csv_CrashRiskAssets, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,crashPredicted,assetId,assetUniqueId,assetName,' \
            'ipAddress,productId,productFamily,softwareRelease,softwareType,serialNumber,risk,endDate'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_crash_risk_factors(partner):
    logger(INFO, f"    Processing Crash Risk Factors .....................", end="")
    with open(pcx_csv_CrashRiskFactors, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,assetId,assetUniqueId,factor,factorType'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_crash_risk_similar_assets(partner):
    logger(INFO, f"    Processing Crash Risk Similar Assets Reports ......", end="")
    with open(pcx_csv_CrashRiskSimilarAssets, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,crashPredicted,assetId,assetUniqueId,assetName,' \
            'productId,productFamily,softwareRelease,softwareType,serialNumber,risk,feature,' \
            'similarityScore'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return

def pcx_crash_risk_last_crashed(partner):
    logger(INFO, f"    Processing Crash Risk Last Reports ................", end="")
    with open(pcx_csv_CrashRiskAssetsLastCrashed, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,daysLastCrashed,assetId,assetUniqueId,assetName,' \
            'productId,productFamily,softwareRelease,softwareType,serialNumber,firstCrashDate,' \
            'lastCrashDate,crashCount,ipAddress'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_crash_risk_crash_history(partner):
    logger(INFO, f"    Processing Crash Risk History .....................", end="")
    with open(pcx_csv_CrashRiskAssetCrashHistory, 'w', encoding='utf-8', newline='') as target:
        CSV_Header = 'customerId,customerName,successTrackId,assetUniqueId,resetReason,timeStamp'
        writer = csv.writer(target, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_Header.split(','))

    logger(INFO, 'SNTC Data Not Available')
    return
    
def pcx_all_risk_reports(partner):
    pcx_crash_risk_assets(partner)
    pcx_crash_risk_factors(partner)
    pcx_crash_risk_similar_assets(partner)
    pcx_crash_risk_last_crashed(partner)
    pcx_crash_risk_crash_history(partner)

#####################################################################
############ Main driver functions to generate PCX data #############
#####################################################################
#
def process_partner_data(partner):
    processed_customer_ids = set()
    logger(INFO, f"*\n*\n*************** BEGIN PCX with Some SNTC Data *************** ")

    # Create the Customers and AllCustomers files
    # 	Customers.csv
    # 	All_Customers.csv
    logger(INFO, f"Creating Customer Reports:")
    pcx_customers(partner)

    # Various reports related to devices
    logger(INFO, f"Creating Device Reports:")
    pcx_all_device_reports(partner)

    logger(INFO, f"*\n*\n*************** BEGIN PCX Meta Data *************** ")
    # Create success track and lifecycle
    logger(INFO, f"Creating ST/LC Templates:")
    pcx_successtracks(partner)
    pcx_lifecycle(partner)
    pcx_compliance_optin(partner)

    logger(INFO, f"*\n*\n*************** BEGIN PCX with NO SNTC Data *************** ")
    # Partner and Partner Offers
    pcx_all_device_lic_reports(partner)

    # Partner and Partner Offers
    logger(INFO, f"Creating Offer Reports:")
    pcx_all_offers(partner)

    # Contracts and details
    logger(INFO, f"Creating Contracts Reports:")
    pcx_all_contracts(partner)

    # Compliance data
    logger(INFO, f"Creating Compliance Reports:")
    pcx_all_compliance_reports(partner)

    # Functions to get the Optimal Software Versions
    logger(INFO, f"Creating Software Reports:")
    pcx_all_software_reports(partner)
    
    # Functions to get the Software Insights
    logger(INFO, f"Creating Software Group Reports:")
    pcx_all_software_groups(partner)
    
    # Functions to get the Automated Fault Management data
    logger(INFO, f"Creating Automated Fault Management Reports:")
    pcx_all_afm_reports(partner)

    # Functions to get the Crash Risk data
    logger(INFO, f"Creating Risk Reports:")
    pcx_all_risk_reports(partner)

'''
Begin main application control
=======================================================================
'''
if __name__ == '__main__':

    # setup parser
    parser = argparse.ArgumentParser(description="Your script description.")
    parser.add_argument("partner", nargs='?', default='', help="Partner name")
    parser.add_argument("-log", "--log-level", default="INFO", help="Set the logging level (default: INFO)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print log message to console")

    # Parse command-line arguments
    args = parser.parse_args()
    partner = args.partner
    verbose = args.verbose

    # create a per-partner folder for saving data
    if partner:
        pcx_folder = partner + '_Insights'
        os.makedirs(pcx_folder, exist_ok=True)
        os.chdir(pcx_folder)
        temp_storage()

    else:
        usage()
        sys.exit()

    # setup the logging level
    init_logger(args.log_level.upper(), verbose)

    logger(INFO, "Retrieving Cisco SuccessTrack UseCase Data")
    ciscoUseCases = read_csv_list(pcx_csv_usecases)

    # now create all the PCX file for each customer
    process_partner_data(partner)

# end
