from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import undetected_chromedriver as uc
import spacy
import os
import logging

from selenium.webdriver.support.wait import WebDriverWait

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Load the spaCy pipmodel
nlp = spacy.load("de_core_news_md")

# Define exclusion terms
# exclusion_terms = [
#     "Öffentlicher Bereich", "Öffentliche Verwaltung", "Öffentlicher Dienst", "Bankensektor",
#     "Public sector", "Public administration", "Public service", "Banking sector"
# ]

model_name_de = "de_core_news_md"
model_name_en = "en_core_web_md"

try:
    nlp_de = spacy.load(model_name_de)
except OSError:
    model_path_de = os.path.join(os.path.dirname(__file__), model_name_de)  # Look in the same directory
    nlp_de = spacy.load(model_path_de)

try:
    nlp_en = spacy.load(model_name_en)
except OSError:
    model_path_en = os.path.join(os.path.dirname(__file__), model_name_en)  # Look in the same directory
    nlp_en = spacy.load(model_path_en)


def contains_exclusion_terms(text, exclusion_terms):
    text_lower = text.lower()
    for term in exclusion_terms:
        if term.lower() in text_lower:
            return True
    return False

def is_similar(keyword_doc, text_doc, threshold=0.7):
    if not keyword_doc or not text_doc:
      return False
    return keyword_doc.similarity(text_doc) > threshold

def process_text(nlp, text):
    try:
        return nlp(text)
    except Exception as e:
        logging.error(f"Error processing text '{text}': {e}", exc_info=True)
        return None
def scrape_gulp(df, threshold, exclusion_terms):
    driver = None # initialize to None for the try-finally block
    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=chrome_options)
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
                    continue # Skip this keyword and continue with the next

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

                     keyword_doc = process_text(nlp_de, keyword)  # process keyword once
                     title_doc = process_text(nlp_de, title) # process title once
                     description_doc = process_text(nlp_de, description) # process description once

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
      logging.error(f"Error in scraping gulp {e}", exc_info=True)
      return pd.DataFrame()
    finally:
        if driver:
            driver.quit()

# Check if the text contains exclusion terms
# def contains_exclusion_terms(text, exclusion_terms):  # Modified function
#     for term in exclusion_terms:
#         if term.lower() in text.lower():
#             return True
#     return False
#
#
# # Check for semantic similarity
# def is_similar(keyword, text):
#     keyword_doc = nlp(keyword)
#     text_doc = nlp(text)
#     return keyword_doc.similarity(text_doc) > 0.7
#
#
# # Gulp scraping logic
# def scrape_gulp(df, threshold, exclusion_terms):
#     chrome_options = uc.ChromeOptions()
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     driver = webdriver.Chrome(options=chrome_options)
#
#     base_url = "https://www.gulp.de/gulp2/g/projekte?query={}"
#
#     for index, row in df.iterrows():
#         if row.isnull().all() or pd.isna(row['Stichworte']) or row['Stichworte'].strip() == "":
#             continue
#
#         keywords = row['Stichworte'].split(';')
#         found_links = []
#
#         for keyword in keywords:
#             search_url = base_url.format(keyword.strip().replace(' ', '%20'))
#             driver.get(search_url)
#             driver.implicitly_wait(10)
#
#             results = driver.find_elements(By.CSS_SELECTOR, '.list-result-item')
#             for result in results:
#                 title_element = result.find_element(By.CSS_SELECTOR, 'h1 a')
#                 title = title_element.text
#                 description = result.find_element(By.CSS_SELECTOR, '.description').text
#
#                 if contains_exclusion_terms(title, exclusion_terms) or contains_exclusion_terms(description,
#                                                                                                 exclusion_terms):
#                     continue
#
#                 if is_similar(keyword, title) or is_similar(keyword, description):
#                     found_links.append(title_element.get_attribute('href'))
#
#         for i, link in enumerate(found_links):
#             df.at[index, f'Link_{i + 1}'] = link
#
#     driver.quit()
#     return df