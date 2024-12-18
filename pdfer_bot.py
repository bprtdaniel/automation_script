
############################################################################################################



# This is the main 'frontend' script that will be run to print the PDFs. It will call the full_pdfer function from the pdf_helpers.py script.



# Ideas to make this better:

# Replace the csv with an automated process.
# Host the code on a simple website, can be flask, where the user simply inputs their folder and precincts. These can be stored in a database.
    # DB can also be adjusted dynamically.
# Run the function windowless, to minmize interaction errors.

############################################################################################################







import csv, time, requests, zipfile, json, os, glob, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
import pandas as pd
import pygsheets
from datetime import datetime
from datetime import timedelta
import vanpy
from van_utility import get_table_contents, fill_multi_select_2, wait_until_clickable_and_click, wait_until_clickable_and_select_by_text, wait_until_clickable_clear_and_fill
from van_utility import wait_until_clickable_and_click_xpath, wait_until_not_visible
from pdf_helpers import full_pdfer
import json
import sys
import time




# This section provides the user with the ability to choose which folders to print, and what settings to use for each folder.

###################################
###################################


# Which folders do you want to print? This needs to be the exact name of the folder in HW.org and the underlying csv.
folders_chosen = ["R11_FolderGOTV"]


# Set the print settings for this folder. Make sure to use the exact name of the settings in HW.org.
# Any desired, additional setting can be set/removed here.

print_settings = {
    "REPORT_FORMAT": '[OHCC] GOTV DVC (No additional IDs)',
    "MINIVAN_CAMPAIGN": '[Turfed] Canvassing - GOTV',
    "Contacted How": "Walk",
    # "Script": "[Turfed] Canvassing - Persuasion",
}


###################################
###################################











### This will run the actual print job.






### Setting the download destination
download_destination = r"download-folder"
# Create download directory if it doesn't exist
os.makedirs(download_destination, exist_ok = True)



# Access the csv to load each precinct and its corresponding folder
turf_tracker = pd.read_csv("csv-destination")
precincts_all= turf_tracker[["Naming Convention"]]
folders_all= turf_tracker[["VAN Folder"]]
# convert to list
precinct_list = precincts_all["Naming Convention"].tolist()
folder_list = folders_all["HW.org Folder"].tolist()
# Get all chosen precincts into a dictionary with their folder
# key: folder value: precincts
precincts_dict = {}

for i in range(len(precinct_list)):
    folder = folder_list[i]
    precinct = precinct_list[i]
    
    if folder in folders_chosen:
        if folder in precincts_dict:
            precincts_dict[folder].append(precinct)
        else:
            precincts_dict[folder] = [precinct]

# Intervention for folders to be printed
print("The folders to print are: ", folders_chosen)
print("Are these the correct folders? (y/n)")
answer = input()
if answer == "n":
    print("Something is wrong, stopping the print here")
    exit()
else:
    print("Ok cool, let's move on")

# Get total precinct count for this folder
total_precinct_count = sum(len(precinct) for precinct in precincts_dict.values())

# Intervention for number of precincts to be printed
print(f"We are going to print {total_precinct_count} precincts for this folder: {folders_chosen}")
print(f"Please check in the csv, if this is the correct number, then hit (y/n)")

answer = input()
if answer == "n":
    print(f"Okay looks like we have a problem here, thanks for catching that, stopping the print")
    exit()
else:
    print("Cool, let's keep going")



# Intervention for the print settings
print("The print settings for this folder are: ", print_settings)
print("Are these the correct print settings? Please check in the turf tracker. If so, we will PRINT NOW, THIS IS THE LAST CHECK (y/n)")

answer = input()
if answer == "n":
    print("Something is off here, stopping the print")
    exit()
else:
    print("Great, go ahead. A HW.org window will open up now, please do not interact with it.")


# Load the JSON file with the secrets in a try-except block
try:
    secrets = json.load(open('secrets.json'))
except IOError as e:
    print(f"No secrets file found. Error: {e}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Secrets file is not valid JSON. Error: {e}")
    sys.exit(1)


# Assign the secrets to variables, wrap in try-except block to catch missing keys
try:
    action_id_email = secrets['van']['User']['user']
    action_id_pw = secrets['van']['User']['password']
    action_id_2fa = secrets['van']['User']['2fa']
except KeyError as e:
    print(f"KeyError: Missing key {e} in secrets file.")
    sys.exit(1)

start_time = time.time()
full_pdfer(download_destination, action_id_email, action_id_pw, action_id_2fa, folders_chosen, print_settings, precincts_dict, total_precinct_count)

print("All done, the PDFs should be ready for bulk download in 'MyPDFs' in HW.org")

end_time = time.time()
execution_time = end_time - start_time
print(f"It took: {execution_time} seconds to complete the print with this many precincts: {total_precinct_count}")