from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import spacy
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load SpaCy models
model_name_de = "de_core_news_md"
model_name_en = "en_core_web_md"

try:
    nlp_de = spacy.load(model_name_de)
except OSError:
    model_path_de = os.path.join(os.path.dirname(__file__), model_name_de)
    nlp_de = spacy.load(model_path_de)

try:
    nlp_en = spacy.load(model_name_en)
except OSError:
    model_path_en = os.path.join(os.path.dirname(__file__), model_name_en)
    nlp_en = spacy.load(model_path_en)


# Utility functions
def contains_exclusion_terms(text, exclusion_terms):
    """Check if the text contains any exclusion terms."""
    text_lower = text.lower()
    for term in exclusion_terms:
        if term.lower() in text_lower:
            return True
    return False


def is_similar(keyword_doc, text_doc, threshold=0.7):
    """Check if two SpaCy docs are similar."""
    if not keyword_doc or not text_doc:
        return False
    return keyword_doc.similarity(text_doc) > threshold


def process_text(nlp, text):
    """Process text using SpaCy NLP model."""
    try:
        return nlp(text)
    except Exception as e:
        logging.error(f"Error processing text '{text}': {e}", exc_info=True)
        return None


# Setup Selenium WebDriver with headless Chrome
def setup_driver():
    """Set up Selenium WebDriver with Chrome in headless mode."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS-level security
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome resource limitations
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    # Path to Chromedriver (matches Dockerfile setup)
    chromedriver_path = "/usr/local/bin/chromedriver"
    service = Service(chromedriver_path)

    # Return configured WebDriver
    return webdriver.Chrome(service=service, options=chrome_options)


# Gulp scraping function
def scrape_gulp(df, threshold, exclusion_terms):
    driver = None
    try:
        driver = setup_driver()  # Initialize WebDriver
        base_url = "https://www.gulp.de/gulp2/g/projekte?query={}"

        for index, row in df.iterrows():
            if row.isnull().all() or pd.isna(row['Stichworte']) or not row['Stichworte'].strip():
                continue

            keywords = [keyword.strip() for keyword in row['Stichworte'].split(';')]
            found_links = []

            for keyword in keywords:
                logging.info(f"Searching for keyword: {keyword}")
                search_url = base_url.format(keyword.replace(' ', '%20'))

                try:
                    driver.get(search_url)
                    WebDriverWait(driver, 30).until(
                        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '.list-result-item'))
                    )
                except TimeoutException as e:
                    logging.error(f"Timeout error for keyword {keyword}: {e}", exc_info=True)
                    continue  # Skip this keyword

                results = driver.find_elements(By.CSS_SELECTOR, '.list-result-item')

                for result in results:
                    try:
                        title_element = result.find_element(By.CSS_SELECTOR, 'h1 a')
                        title = title_element.text
                        description_element = result.find_element(By.CSS_SELECTOR, '.description')
                        description = description_element.text

                        if contains_exclusion_terms(title, exclusion_terms) or contains_exclusion_terms(description, exclusion_terms):
                            logging.info(f"Skipping project due to exclusion terms: {title}")
                            continue

                        keyword_doc = process_text(nlp_de, keyword)
                        title_doc = process_text(nlp_de, title)
                        description_doc = process_text(nlp_de, description)

                        if is_similar(keyword_doc, title_doc, threshold) or is_similar(keyword_doc, description_doc, threshold):
                            link = title_element.get_attribute('href')
                            found_links.append(link)
                            logging.info(f"Found matching link: {link} with keyword {keyword}")

                    except (NoSuchElementException, Exception) as e:
                        logging.error(f"Error processing a single result: {e}", exc_info=True)
                        continue

            for i, link in enumerate(found_links):
                df.at[index, f'Link_{i + 1}'] = link

        return df

    except Exception as e:
        logging.error(f"Error in scraping gulp: {e}", exc_info=True)
        return pd.DataFrame()

    finally:
        if driver:
            driver.quit()  # Always quit the driver
