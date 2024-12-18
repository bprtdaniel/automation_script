
############################################################################################################



# This is a Proof of Concept (POC) script for software automation.
# The goal is to use Selenium to automate the process of automatically pdf-ing a set of pdfs from the software/wbsite.


# Process

# 1. Log into the website
# 2. Navigate to the correct page
# 3. Select the correct folders
# 4. Select the correct precincts
# 5. Print the precincts with the correct settings
# 6. Repeat for all precincts


# Currently, the selection process for the precincts and folders is manual and depends on a dictionary-style csv that needs to be amended to the project directory.
# The precincts_dict is a dictionary that holds the folder names as keys and the precincts as values.



# This script builds the function itself, which will be called in the main bot script.
# See pdfer_bot.py for the 'frontend' script.


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
from selenium.common.exceptions import TimeoutException
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
import pygsheets
import json
import sys


def full_pdfer(download_destination, website_id_email, website_id_pw, website_id_2fa, folders_chosen, print_settings, precincts_dict, total_precinct_count):
    '''
    download_destination: where pdfs will be downloaded to
    website_id_email: email for the website
    website_id_pw: password for the website
    website_id_2fa: 2fa for the website
    folders_chosen: folders to be printed, this is variable that will be defined in the actual pdfing bot
    print_settings: print settings, also defined and called in the bot
    precincts_dict: dictionary of precincts to be printed, withing a folder each
    total_precinct_count: total number of precincts to be printed, this is a sum of all precincts in the precincts_dict. Inserted as a check.
    '''




    service = Service(ChromeDriverManager().install())
    # Call options
    options = Options()

    # Set preferences
    prefs = {
        "download.default_directory": download_destination, # Set the default download directory to the download_destination
        "download.prompt_for_download": False, 
        "download.directory_upgrade": True,
    }
    options.add_experimental_option("prefs", prefs) # pass the preferences to the options object
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("www.hypotheticalwebsite.org") # call the website hypotheticalwebsite.org = HW.org

    # First step is to automatically log into the website, accounting for the 2FA


    # set 2fa to true/false
    twofa = True

    # Log in

    # enter email from a JSON secrets file
    # Needs to be set up in the same directory as the script
    enter_email = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'email-ID'))
    )
    enter_email.send_keys(website_id_email)

    # enter password from JSON secrets file
    enter_pw = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'password-css'))
    )
    enter_pw.send_keys(website_id_pw)

    # click submit
    click_submit = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'submit-css'))
    )
    click_submit.click()

    # Now, we need to account for the 2FA
    # website_id_2fa needs to be extracted from the QR code that is used to set up the 2FA in the first place.
    if twofa:
        attempts = 0
        # initiate code as empty string
        code = ""

        while attempts < 6 and not code:
            authcode = subprocess.check_output(['python',  '-m', 'oathtool', str(website_id_2fa)])
            authcode_parsed = str(int(authcode))

            # check if the authcode is 6 digits long, else wait 30 seconds and try again
            if len(authcode_parsed) != 6:
                code = ""
                attempts += 1
                time.sleep(30)
            else:
                code = int(authcode_parsed)

        if not code:
            raise Exception("Auth Code could not be generated")

        # enter code
        enter_twfa = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'code-ID'))
        )
        enter_twfa.send_keys(code)
        time.sleep(2)

    wait_until_clickable_and_click(driver, '[name=action')



    #####

    # add a section to click a next button if it exists
    # this sometimes appears, sometimes doesn't, add a check for it via TimeoutException
    time.sleep(1)


    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "next-ID"))
        )
        next_button.click()
    except TimeoutException:
        print("No next button, proceeding")
    

    time.sleep(1)

    ##########################
    # Addings some specific navigation steps to get to the right page

    myv_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Specific_tab-Link"))
    )
    myv_tab.click()
    # open sidebar
    sidebar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "sidebar-name"))
    )
    sidebar.click()
    # click MyTurfs
    MyFolders = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "Folders_xpath"))
    )
    MyFolders.click()


    # Clear the filters if applied

    try:
        clear_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "clea-xpath"))
        )
        clear_button.click()
        print("Filters cleared.")
    except TimeoutException:
        print("No filters, proceeding")



    time.sleep(1)

    # Click "edit"
    edit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "edit-xpath"))
    )
    edit_button.click()

    time.sleep(1)

    # Click the dropdown to start the folder filter process
    send_folders = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "send-ID"))
    )
    send_folders.click()


    # This is a dynamic dropdown, so the results will only appear in the HTML once clicked.
    # We can't select by ID in the HTML here, so we move to typing the folder name into the dropdown and hitting enter instead.

    for folder in folders_chosen:
        try:
            # Select first (or only) folder here and assign it to be sent as a key
            send_folders.send_keys(folder)

            # Type that folder via the key and hit enter so it becomes available
            send_folders.send_keys(Keys.ENTER)

        except Exception as e:
            print(f"Error selecting folder '{folder}': {e}")

    time.sleep(3)


    # Remember filters
    remember_filters = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "remember-ID"))
    )
    remember_filters.click()

    time.sleep(3)

    # Select all turfs within the folder at once
    tick_checkbox = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "checkbox-ID"))
    )
    tick_checkbox.click()

    time.sleep(3)

    # If an additional page exists, click it, wait, click select all again

    # try:
    #     next_page = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.CLASS_NAME, "ngPagerControl ng-scope active"))
    #     )
    #     next_page.click()

    #     time.sleep(3)

    #     tick_checkbox = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.CLASS_NAME, "ngSelectionHeader"))
    #     )
    #     tick_checkbox.click()

    # except TimeoutException:
    #     print("No additional page, let's go on")


    # Click "Quick Actions"
    quick_actions = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "quick_actions-ID"))
    )  
    quick_actions.click()   

    # Select print
    select_print = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "hit_print-xpath"))
    )
    select_print.click()


    # Adding the first check here, to see if the number of turfs in VAN == the number of turfs in the CSV
    # Precinct match is an internal check
    # The match between local and website can be off
    # Turf number is much higher than precinct number, as it includes all the precincts in the turfs

    print(f"We want to print {total_precinct_count} turfs from this folder, this should be the same number as on screen")
    # Ask if we are seeing this number on screen
    print(f"Are you seeing on the website that we are going to print {total_precinct_count} Map Regions? The Turf Number is most probably higher than that and that's fine (y/n)")
    answer = input()
    if answer == "n":
        print("Stopping the pdfing")
        print("If the terminal number is > website number, then the difference is the amount of Precincts that don't show up as cut on website. If the terminal number is < website number, then there are too many turfs on the website")
        exit() # This will stop the script
    else:
        print("Okay, this seems to be fine, carry on")
    

    # Inserting some time to manually check if the correct number of turfs is selected
    time.sleep(3)


    # This concludes the section from login to right before printing.
    # The next section needs a check to see if the number of turfs on website == turfs in the CSV

    # click "Next"
    click_next = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "next-ID"))
    )
    click_next.click()


    # Enter the print settings
    ReportFormat = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "Report_Format-ID"))
    )
    ReportFormat.send_keys(print_settings["REPORT_FORMAT"])

    time.sleep(1)

    # We will print without the Script for now

    # Script = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolderVANPage_VanDetailsItemActiveScriptID_VANInputItemDetailsItemActiveScriptID_ActiveScriptID"))
    # )
    # Script.send_keys(print_settings["Script"])

    time.sleep(1)

    ContactedHow = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "Contacted_how-ID"))
    )
    ContactedHow.send_keys(print_settings["Contacted How"])

    time.sleep(1)

    MiniCampaign = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "MiniCampaign-ID"))
    )
    MiniCampaign.send_keys(print_settings["MINI_CAMPAIGN"])


    time.sleep(5)

    # Add a check here, if the settings are correct, before proceeding to print

    # THIS CAN BE A MANUAL CHECK FOR NOW


    # THIS IS THE PRINTING PROCESS. ONE BY ONE IT WILL ITERATE TO THE NEXT PRECINCT AND SET THE PRINT SETTINGS


    # THIS WILL PRINT AS MANY PRECINCTS AS THERE ARE IN THE DICTIONARY

    print_counter = 0

    for folder, precincts in precincts_dict.items():  
        # Add overview which folders are going to be printed as a check
        print(f"We are going to print {folders_chosen}")

        # Show number of precincts in each folder as a check
        print(f"Folder: {folder} holds {len(precincts)} precincts")
        
        for idx, precinct in enumerate(precincts, start=1):
            try:
                # Precinct is now just a string, so we use it directly
                precinct_name = precinct

                print(f"Printing precinct '{precinct_name}' in folder '{folder}'")

                Print_Next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "NextID"))
                )
                Print_Next_button.click()

                print_counter += 1

                print(f"Printing Currently at: {print_counter}. We are {print_counter / total_precinct_count * 100:.2f}% done for the selected folder(s)")

                time.sleep(2) # This is needed, so we don't get caught by the website. At 1 second, we do get caught.
            except Exception as e:
                # Print the current precinct name in case of failure
                print(f"FAILURE TO PRINT PRECINCT '{precinct_name}' IN FOLDER '{folder}': {e}")

    # Final print summary
    if print_counter == total_precinct_count:
        print("All precincts printed successfully, very demure, wow")
    else:
        print("SOMETHING BROKE YOU ARE NOT ENOUGH OF A DEMURE PERSON. FIX ASAP")
        