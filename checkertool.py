import logging
import smtplib
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)-8s %(message)s')

def send_keys_delay(controller,keys,delay=0.1):
    for key in keys:
        controller.send_keys(key)
        sleep(delay)

email = "youremail@gmail.com"
zipcode = "yourzipcode"
max_distance = "10"

options = Options()
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--incognito")
options.add_argument("disable-infobars")
options.add_argument("start-maximized")
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--no-sandbox')
options.add_argument("--disable-web-security")
options.add_argument("--disable-xss-auditor")
options.add_argument('log-level=3')
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
action = ActionChains(driver)

attempts=0

def checker():
    global attempts, max_distance

    message = ""
    
    while True:
        attempts+=1
        logging.info(f"Search #{attempts}")
        driver.get("https://satsuite.collegeboard.org/sat/test-center-search")
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "apricot_input_5"))
            )
        except TimeoutException:
            logging.error("Zip code input field not loaded in time")
            continue
        zipcode_input = driver.find_element(By.ID, "apricot_input_5")
        send_keys_delay(zipcode_input, zipcode)
        dropdown = Select(driver.find_element(By.ID, "apricot_select_6"))
        dropdown.select_by_value(max_distance)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="test-center-search"]/div[1]/div/div/div/div[2]/button'))
            )
            sleep(1)
            find_center = driver.find_element(By.XPATH, '//*[@id="test-center-search"]/div[1]/div/div/div/div[2]/button')
            find_center.click()

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            sleep(20)

        try:
            available_centers = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Test centers with available seats")]'))
            )
            
            num_available_centers = int(available_centers.text.split('(')[1].split(')')[0])
            
            if num_available_centers == 0:
                logging.info(f"No available testing centers found within {max_distance} miles. :(")
                sleep(300)
                continue

            else:
                logging.info(f"Testing Center(s) Found!")
                available_centers.click()
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sat-tc-card"))
                    )
                    test_centers = driver.find_elements(By.CLASS_NAME, "sat-tc-card")
                    
                    for center in test_centers:
                        seat_availability = center.find_element(By.CLASS_NAME, "seat-availability").text.strip()
                        if "Seat Is Available" in seat_availability:
                            name = center.find_element(By.CLASS_NAME, "cb-card-title").text.strip()
                            distance_paragraphs = center.find_elements(By.XPATH, ".//div[p[@class='cb-card-desc']]/p")
                            if len(distance_paragraphs) > 1:
                                distance = distance_paragraphs[1].text.strip()
                            else:
                                distance = "Distance not specified"
                            logging.info(f"Location #{test_centers.index(center)+1}: {name}, {distance}")
                            message += f'Location #{test_centers.index(center)+1}: {name}, {distance}\n'
                    send_email(message)
                    return

                except Exception as e:
                    logging.error("An error occurred: " + str(e))
                    sleep(20)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            sleep(20)

def send_email(email_content):
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(email, "yourapppassword")  # watch this tutorial on how to get one https://www.youtube.com/watch?v=J4CtP1MBtOE
        text = f"Subject: SAT Testing Center Availability Found!\n\n{email_content}"
        s.sendmail(email, email, text)
        s.quit()
    except Exception as e:
        logging.error("Failed to send email: " + str(e))

checker()