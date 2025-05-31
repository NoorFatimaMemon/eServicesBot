from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
import os
import pandas as pd
import logging

class HandyWrappers:
    # Check if an element exists
    def element_exists(self, driver, timeout, xpath):
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return True
        except TimeoutException: 
            return False

    # Click an element safely
    def click_element(self, driver, timeout, xpath):
        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except TimeoutException:
            logging.warning(f"Element not clickable: {xpath}")
        
    # Input text into a field safely
    def input_text(self, driver, timeout, xpath, text):
        try:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element.clear()
            element.send_keys(text)
        except TimeoutException:
            logging.warning(f"Failed to input text in: {xpath}")
    
    # Retrieve text from an element safely
    def get_text(self, driver, timeout, xpath):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath))).text
        except TimeoutException:
            logging.warning(f"Failed to retrieve text from: {xpath}")
            return None
        
    def _get_text_safe(self, driver, xpath):
        """Utility to safely get text with fallback to None."""
        try:
            return self.get_text(driver, 30, xpath)
        except Exception as e:
            logging.warning(f"Failed to get text from {xpath}: {e}")
            return None
        
    # Scroll to an element using its XPath
    def scroll_to_element(self, driver, timeout, xpath):
        try:
            element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
        except TimeoutException:
            logging.warning(f"Failed to scroll to element: {xpath}")

    # calendar filling input method
    def date_input(self, driver, timeout, xpath, date_value):
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        calendar_input = driver.find_element(By.XPATH, xpath)
        calendar_input.click()
        calendar_input.send_keys(Keys.CONTROL, 'a')  # For Windows/Linux
        calendar_input.send_keys(date_value)

    # to create excel file for the output
    def xlsx_creator(self, file_path):
        headers = ['ELIGIBILITY', 'INSURANCE NAME', 'NAME', 'MEDICARE ID', 
                   'DOB', 'ADDRESS', 'CITY', 'STATE', 'ZIP']

        if os.path.exists(file_path):
            print("The file exists.")
            df = pd.read_excel(file_path)
            if 'MEDICARE ID' in df.columns:
                medicare_ids = df['MEDICARE ID'].tolist()
                print(f"Already Scraped MEDICARE IDs are: {medicare_ids}")
                return medicare_ids
            else:
                print("Column 'MEDICARE ID' not found in the Excel file.")
                return None
        else:
            print("The file does not exist. Therefore, creating one.")
            df = pd.DataFrame(columns=headers)
            df.to_excel(file_path, index=False)
            return None

    def excel_reader(self, input_data_filename):
        try:
            df = pd.read_excel(input_data_filename)
            if 'MEDICARE ID' in df.columns:
                return df['MEDICARE ID'].tolist()
            else:
                logging.error("'MEDICARE ID' column not found in the Excel file.")
                return []
        except Exception as e:
            logging.error(f"Error loading Medicare IDs: {e}")
            return []

    # to get name and DOB name of corresponding id    
    def get_info_by_medicare_id(self, medicare_id, input_data_filename):
        try:
            df = pd.read_excel(input_data_filename)
            if 'MEDICARE ID' not in df.columns:
                logging.error("'MEDICARE ID' column not found in the Excel file.")
                return None

            row = df[df['MEDICARE ID'] == medicare_id]
            if not row.empty:
                name = row.iloc[0]['NAME']
                dob_raw = row.iloc[0]['DOB']
                dob = self.format_date(dob_raw)
                return name, dob
            else:
                logging.warning(f"Medicare ID '{medicare_id}' not found in the Excel file.")
                return None

        except Exception as e:
            logging.error(f"Error retrieving information for Medicare ID {medicare_id}: {e}")
            return None

    def format_date(self, dob):
        try:
            # If dob is already a datetime object, format it
            if isinstance(dob, datetime):
                return dob.strftime("%m/%d/%Y")
            
            elif isinstance(dob, str):
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"):
                    try: return datetime.strptime(dob.strip(), fmt).strftime("%m/%d/%Y")
                    except ValueError: continue  
                print(f"Failed to parse string '{dob}' into a date")
                return dob
            
            elif isinstance(dob, (int, float)):
                return (datetime(1899, 12, 30) + timedelta(days=dob)).strftime("%m/%d/%Y")
            
            else:
                print(f"Unsupported type: {type(dob)}")
                return dob

        except Exception as e:
            print(f"Error: {e}")
            return None
