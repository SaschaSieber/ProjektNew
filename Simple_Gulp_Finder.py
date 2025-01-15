import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import undetected_chromedriver as uc

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Set up Selenium WebDriver with Chrome options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource issues
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")

    # Initialize WebDriver with the given options
    service = Service("/usr/local/bin/chromedriver")  # Path to ChromeDriver binary
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def contains_exclusion_terms(text, exclusion_terms):
    text_lower = text.lower()
    for term in exclusion_terms:
        if term.lower() in text_lower:
            return True
    return False

def process_result(result, exclusion_terms):
    try:
        title_element = result.find_element(By.CSS_SELECTOR, 'h1 a')
        title = title_element.text.strip()
        description_element = result.find_element(By.CSS_SELECTOR, '.description')
        description = description_element.text.strip()
        logging.info(f"Found Project: {title}")
        if contains_exclusion_terms(title, exclusion_terms) or contains_exclusion_terms(description, exclusion_terms):
            logging.info(f"Skipping project due to exclusion terms: {title}")
            return None
        link = title_element.get_attribute('href')
        logging.info(f"Found link: {link}")
        return link
    except NoSuchElementException as e:
        logging.error(f"Error finding element: {e}, skipping this result", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"Error processing a single result: {e}, skipping this result", exc_info=True)
        return None

def scrape_gulp(df, exclusion_terms):
    driver = None  # Initialize to None for the try-finally block
    try:
        driver = setup_driver()  # Use the setup_driver function
        base_url = "https://www.gulp.de/gulp2/g/projekte?query={}"
        timeout = 10  # seconds

        for index, row in df.iterrows():
            if row.isnull().all() or pd.isna(row['Stichworte']) or not row['Stichworte'].strip():
                continue

            keywords = [keyword.strip() for keyword in row['Stichworte'].split(';')]
            found_links = []

            for keyword in keywords:
                logging.info(f"Searching for keyword: {keyword}")
                search_url = base_url.format(f'"{keyword.replace(" ", "%20")}"')
                try:
                    driver.get(search_url)
                    WebDriverWait(driver, timeout).until(
                        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '.list-result-item'))
                    )

                except TimeoutException as e:
                    logging.error(f"Timeout error for keyword {keyword}: {e} No links found", exc_info=True)
                    continue

                results = driver.find_elements(By.CSS_SELECTOR, '.list-result-item')
                logging.info(f"Found {len(results)} results for keyword '{keyword}'")

                for result in results:
                    link = process_result(result, exclusion_terms)
                    if link:
                        found_links.append(link)

            for i, link in enumerate(found_links):
                df.at[index, f'Link_{i + 1}'] = link
        return df
    except Exception as e:
        logging.error(f"Error in scraping gulp {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        if driver:
            driver.quit()  # Ensure the WebDriver is closed
