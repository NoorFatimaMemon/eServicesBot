from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException
from datetime import date
from Helpers import HandyWrappers
import pandas as pd
import logging
import time
import json
import os

class AutomationBot:
    HW = HandyWrappers()

    def loading_URL(self, driver, url, timeout=100):
        """Open a URL with error handling."""
        try:
            logging.info(f"Opening URL -------------------------------> {url}")
            while True:
                # Check if URL is loaded correctly or not to break the loop
                if self.HW.element_exists(driver, 5, '//input[@name="userId"]'):
                    break
                driver.get(url)
                driver.implicitly_wait(timeout)
        except TimeoutException:
            logging.error('-----------------------PAGE LOAD TIMED OUT!-----------------------')
            print("The page took too long to load. Please try again.")

    def portal_login(self, eservices_url, headless, username, password):
        """Log into eServices"""
        logging.info("--------------- Starting new browser session ---------------")
        driver = Driver(uc=True, headless=headless)

        logging.info(f"Accessing -----------------------------> {eservices_url}")
        self.loading_URL(driver, eservices_url, timeout=30)

        try:
            for attempt in range(5):
                logging.info(f'--- LOGIN ATTEMPT {attempt + 1} ---')
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # input credentials
                try:
                    logging.info(f'--- Entering User Credentials---')
                    self.HW.input_text(driver, 15, '//input[@name="userId"]', username)
                    self.HW.input_text(driver, 15, '//input[@name="password"]', password)
                    self.HW.click_element(driver, 10, '//a[@title="Log into eServices"]')
                except TimeoutException:
                    logging.warning("Login fields did not appear properly. Retrying...")
                    continue

                # If login failed, and 'Return to login page' is present, click and scroll again
                if self.HW.element_exists(driver, 5, '//a[.="Return to login page"]'):
                    logging.warning('"Return to login page" found. Resetting login form...')
                    self.HW.click_element(driver, 10, '//a[.="Return to login page"]')
                else:
                    break

            # --- Login code handling ---
            logging.info('Getting Login code and/or saving in json for later.')
            self.get_valid_login_code(driver)
            # Handling dialog box
            logging.info('Checking for dialog box...')
            self.HW.click_element(driver, 100, '//button[.="I ACKNOWLEDGE"]')
            logging.info('Login completed successfully.')
            return driver
        except Exception as e: 
            logging.error(f"Login failed: {e}")
            
    def get_valid_login_code(self, driver):
        """Prompt for and return a valid login code for today, reusing if already saved"""
        code_file = "login_code.json"
        # Load saved code and date from file if it exists
        saved_code, saved_date = None, None
        if os.path.exists(code_file):
            try:
                with open(code_file, 'r') as f:
                    data = json.load(f)
                    saved_code = data.get('code')
                    saved_date = data.get('date')
                    if saved_date:
                        saved_date = date.fromisoformat(saved_date)
            except (json.JSONDecodeError, ValueError):
                logging.warning("Error reading login code file. Starting fresh.")

        today = date.today()
        if saved_date != today: saved_code = None

        while True:
            if saved_code is None:
                try:
                    saved_code = int(input('Enter login code: '))
                    # Save the code and date to file
                    with open(code_file, 'w') as f:
                        json.dump({'code': saved_code, 'date': today.isoformat()}, f)
                except ValueError:
                    print("Please enter a valid numeric code.")
                    continue

            # Input and submit the login code
            self.HW.input_text(driver, 20, '//input[@name="accessCode"]', saved_code)
            self.HW.click_element(driver, 10, '//button[@name="submitAccessCode"]')

            # Check if code is valid
            try:
                if self.HW.element_exists(driver, 5, '//span[contains(normalize-space(text()), "The verification code entered does not match")]'):
                    logging.warning('Invalid login code entered. Please try again.')
                    saved_code = None
                    # Remove invalid code from file
                    if os.path.exists(code_file):
                        os.remove(code_file)
                else: 
                    logging.info('entered login code is correct.')
                    break
            except Exception as e:
                logging.error(f"Error in login code: {e}")
    
    def Automation(self, driver, medicare_id, input_data_filename, output_data_filename):
        self.HW.click_element(driver, 30, "//a[.='Eligibility' and @id='eligibilityTab']")
        self.HW.scroll_to_element(driver, 10, "//h3[.='Beneficiary Information']") 

        name, dob = self.HW.get_info_by_medicare_id(medicare_id, input_data_filename)
        # Extract and sanitize name
        full_name = name.strip().split()
        first_name = full_name[0]
        last_name = full_name[-1] if len(full_name) > 1 else ''

        logging.info('--------- INITIATING Automation PROCESS ---------')
        logging.info('Filling form with patient data...')
        self.HW.input_text(driver, 30, '//input[@name="beneficiaryLastName"]', last_name)
        self.HW.input_text(driver, 30, '//input[@name="beneficiaryFirstName"]', first_name)
        self.HW.input_text(driver, 30, '//input[@name="hicNumber"]', medicare_id)
        self.HW.date_input(driver, 30, '//input[@name="beneficiaryDateOfBirth"]', dob)
        self.HW.scroll_to_element(driver, 20, '//button[.="Submit"]')    
        self.HW.click_element(driver, 20, '//button[.="Submit"]')
        time.sleep(1.5)
        self.HW.scroll_to_element(driver, 50, "//a[.='Eligibility' and @id='eligibilityTab']")  
        eligibility = ''         

        try:
            # Check if DOD or Beneficiary exists
            logging.info('Checking beneficiary status...')
            logging.info("Checking Medicare ID and it's DOD Exists or Not...")
            if self.HW.element_exists(driver, 5, "(//span[span[normalize-space(text())='DOD:']]/text()[normalize-space()])[3]//parent::span"):
                eligibility = 'DEAD'
                insurance_name = address = city = state = zip_code = ''
                logging.info(f"The requested Medicare ID's DOD is Dead. So, Eligibility = '{eligibility}'")

            elif self.HW.element_exists(driver, 5, "//h4[@class='alert-heading']/parent::div//p[contains(normalize-space(.), 'The beneficiary you requested cannot be found. Please verify your information.')]"):
                eligibility = 'ID ERROR'
                insurance_name = address = city = state = zip_code = ''
                logging.info(f"The beneficiary you requested cannot be found. So, Eligibility = '{eligibility}'")

            else:
                # If beneficiary exists, extract details
                logging.info('Extracting detailed information...')
                self.HW.click_element(driver, 20, '//li[@aria-controls="eligibility"]//a[.="Eligibility"]')
                self.HW.scroll_to_element(driver, 30, '(//h3[normalize-space(text())="MDPP Inactive Periods"])[1]')

                # Check inactive period
                logging.info("Checking Medicare ID's Inactive Period Exists or Not...")
                try: 
                    inactive_period = self.HW.get_text(driver, 30, '((//h3[normalize-space(text())="MDPP Inactive Periods"])[1]//ancestor::div[@aria-describedby="mdppinactive"]//div[@class="row margin"]//div)[2]')
                    inactive_period = inactive_period.strip() if inactive_period else ''
                except Exception as e: 
                    print("Error:", e)
                    inactive_period = ''

                if inactive_period: 
                    eligibility = 'INACTIVE PART B'
                    logging.info(f"The Medicare ID's Inactive Period exists. So, Eligibility = '{eligibility}'")

                # Get Address Info
                logging.info('Getting Beneficiary Address Info...')
                address = self.HW._get_text_safe(driver, '((//h3[.="Beneficiary Address"])[1]//ancestor::div[@aria-describedby="beneaddressEliggFields"]//div[@class="row margin"]//div)[2]')
                city = self.HW._get_text_safe(driver, '((//h3[.="Beneficiary Address"])[1]//ancestor::div[@aria-describedby="beneaddressEliggFields"]//div[@class="row margin"]//div)[6]')
                state = self.HW._get_text_safe(driver, '((//h3[.="Beneficiary Address"])[1]//ancestor::div[@aria-describedby="beneaddressEliggFields"]//div[@class="row margin"]//div)[8]')
                zip_code = self.HW._get_text_safe(driver, '((//h3[.="Beneficiary Address"])[1]//ancestor::div[@aria-describedby="beneaddressEliggFields"]//div[@class="row margin"]//div)[10]')
                logging.info('Got *****Address, City, State, Zipcode*****')

                # Insurance info
                logging.info('Getting Insurance Info...')
                self.HW.click_element(driver, 20, '//li[@aria-controls="PalnCoverage"]//a[.="Plan Coverage"]')
                self.HW.scroll_to_element(driver, 30, '(//h3[.="Medicare Part D"])[1]')
                insurance_name = self.HW._get_text_safe(driver, '(((//div[@id="medicarepartDPlanCoverageFields"])[1]//div[@class="row margin"])[2]//span)[4]')
                logging.info('Got *****Insurance Name*****')

                # Determine final eligibility
                logging.info('Determine final eligibility value if not obtained from above values...')
                driver.execute_script("window.scrollTo(0, 0);")
                if eligibility != 'INACTIVE PART B':
                    try:
                        logging.info('Checking Plan Type...')
                        try: 
                            plan_type = self.HW.get_text(driver, 30, '((//p[.="Plan Type:"])[1]//ancestor::div[@class="row margin"]//div)[2]')
                            plan_type = plan_type.strip() if plan_type else ''
                        except Exception as e: 
                            print("Error:", e)
                            plan_type = ''

                        if plan_type: 
                            eligibility = plan_type
                            logging.info('Got *****Eligibility***** from plan type')
                        else:
                            logging.info('Checking MSP because Plan Type does not exists...')
                            self.HW.click_element(driver, 20, '//li[@aria-controls="MSP"]//a[.="MSP"]')
                            try: 
                                msp_insurer_name = self.HW._get_text_safe(driver, '((//h3[normalize-space(text()) ="Medicare Secondary Payer"])[1]//ancestor::div[@aria-describedby="medicaresecondarypayermspFields"]//div[@class="row margin"]//div)[6]')
                                msp_insurer_name = msp_insurer_name.strip() if msp_insurer_name else ''
                            except Exception as e: 
                                print("Error:", e)
                                msp_insurer_name = ''

                            eligibility = "MSP" if msp_insurer_name else 'MED B'
                            logging.info('Got *****Eligibility*****')
                    except:
                        eligibility = 'UNKNOWN'
                        logging.info(f"Nothing worked so Eligibility = '{eligibility}'")

                logging.info(f'Eligibility: {eligibility}, Insurance: {insurance_name}, Address: {address}, City: {city}, State: {state}, ZIP: {zip_code}')

            # Prepare row data
            logging.info('Preparing the Row Data')
            row_df = pd.DataFrame([{'ELIGIBILITY': eligibility, 'INSURANCE NAME': insurance_name,
                                    'NAME': name, 'MEDICARE ID': medicare_id, 'DOB': dob, 'ADDRESS': address, 
                                    'CITY': city, 'STATE': state, 'ZIP': zip_code}])

            logging.info('Storing the Row Data')
            with pd.ExcelWriter(output_data_filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                row_df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
            
            self.HW.click_element(driver, 20, '//a[.="Inquiry"]//parent::li')
        
        except: 
            print(f"Failed to fetch data for {medicare_id}")               
