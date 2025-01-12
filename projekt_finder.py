from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import undetected_chromedriver as uc
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@Language.factory("language_detector")
def create_language_detector(nlp, name):
    return LanguageDetector()

nlp_de = spacy.load("de_core_news_md")
nlp_en = spacy.load("en_core_web_md")
nlp_de.add_pipe("language_detector", last=True)
nlp_en.add_pipe("language_detector", last=True)

# # Define exclusion terms
# exclusion_terms = [
#     "Öffentlicher Bereich", "Öffentliche Verwaltung", "Öffentlicher Dienst", "Bankensektor",
#     "Public sector", "Public administration", "Public service", "Banking sector"
# ]

# Check for exclusion terms
def contains_exclusion_terms(text, exclusion_terms):
    for term in exclusion_terms:
        if term.lower() in text.lower():
            return True
    return False

# Detect language and select spacy model
def detect_language_and_select_model(text):
    doc_de = nlp_de(text)
    doc_en = nlp_en(text)
    return nlp_de if doc_de._.language['language'] == 'de' else nlp_en

# Protip scraping logic

def scrape_protip(df, threshold, exclusion_terms):
    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www.protip.de/projekt-ticker")

        for index, row in df.iterrows():
            if row.isnull().all() or pd.isna(row['Stichworte']) or row['Stichworte'].strip() == "":
                continue

            keyword = row['Stichworte'].strip()
            found_links = []

            titles = driver.find_elements(By.CSS_SELECTOR, '.element.element-itemname a')
            for title in titles:
                try:
                    title_text = title.get_attribute('title')
                    model = detect_language_and_select_model(title_text)

                    if contains_exclusion_terms(title_text, exclusion_terms):
                        logging.info(f"Skipping project due to exclusion terms: {title}")
                        continue

                    if model(keyword).similarity(model(title_text)) > threshold:
                        link = title.get_attribute('href')
                        found_links.append(title.get_attribute('href'))
                        logging.info(f"Found matching link: {link} with keyword {keyword}")
                except Exception as e:

                  print (f"Error with title: {e}")


            for i, link in enumerate(found_links):
                df.at[index, f'Link_{i + 1}'] = link

        driver.quit()
        return df
    except Exception as e:
        print(f"Error in scrape protip: {e}")
        return pd.DataFrame()




#
# def scrape_protip1(df, threshold, exclusion_terms):
#     chrome_options = uc.ChromeOptions()
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     driver = webdriver.Chrome(options=chrome_options)
#
#     driver.get("https://www.protip.de/projekt-ticker")
#
#     for index, row in df.iterrows():
#         if row.isnull().all() or pd.isna(row['Stichworte']) or row['Stichworte'].strip() == "":
#             continue
#
#         keyword = row['Stichworte'].strip()
#         found_links = []
#
#         titles = driver.find_elements(By.CSS_SELECTOR, '.element.element-itemname a')
#         for title in titles:
#             title_text = title.get_attribute('title')
#             model = detect_language_and_select_model(title_text)
#
#             if contains_exclusion_terms(title_text, exclusion_terms):
#                 continue
#
#             if model(keyword).similarity(model(title_text)) > threshold:
#                 found_links.append(title.get_attribute('href'))
#
#         for i, link in enumerate(found_links):
#             df.at[index, f'Link_{i + 1}'] = link
#
#     driver.quit()
#     return df