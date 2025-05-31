from Automation import AutomationBot
from Helpers import HandyWrappers
import logging
# Set up logging configuration for better debugging and monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Main():
    AutBot, HW = AutomationBot(), HandyWrappers()

    def main(self, headless):
        # Credentials & files
        eservices_url = 'https://www.onlineproviderservices.com/ecx_improvev2/'
        username = input('Enter username: ')
        password = input('Enter password: ')
        input_data_filename, output_data_filename = 'Tracking_IDs.xlsx', 'ELG_DATA_Output.xlsx'

        # Checking output excel file exists, if yes, then loading, otherwise, creating new one
        logging.info(f"Checking if excel file {output_data_filename} exists or needs to be created.")
        scraped_medicare_ids = self.HW.xlsx_creator(output_data_filename)

        # Load new Medicare IDs from excel
        logging.info(f"Loading Medicare IDs from {input_data_filename}")
        new_medicare_ids = self.HW.excel_reader(input_data_filename)

        ID_counter = 0
        # Perform login of eServices
        try: 
            driver = self.AutBot.portal_login(eservices_url, headless, username, password)
        except Exception as e: 
            logging.error(f"Error during login: {e}")

        for medicare_id in new_medicare_ids:
            if scraped_medicare_ids is None or medicare_id not in scraped_medicare_ids:
                # Restart browser after every 10 IDs
                if ID_counter > 0 and ID_counter % 10 == 0:
                    driver.quit()
                    logging.info("Restarting browser session after processing 10 IDs.")
                    driver = self.AutBot.portal_login(eservices_url, headless, username, password)

                logging.info(f"Scraping MEDICARE ID: {medicare_id}")
                # Perform Automation
                try: 
                    self.AutBot.Automation(driver, medicare_id, input_data_filename, output_data_filename)   
                except Exception as e:
                    logging.error(f"Error during automation: {e}")

                ID_counter += 1

        # Ensure browser is closed at the end
        if driver:
            driver.quit()
            logging.info("Browser session closed. Scraping completed.")

            
test=Main()
test.main(headless=False)