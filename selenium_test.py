# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 10:08:28 2024

@author: mcveigh
"""
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
#PATH = "C:\Users\mcveigh\Documents\PythonPC\chrome.exe"
#driver = webdriver.Chrome(PATH)
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re


urls = ['https://www.microbiologyresearch.org/content/journal/ijsem/10.1099/ijsem.0.006404',
       'https://www.microbiologyresearch.org/content/journal/ijsem/10.1099/ijsem.0.006406?emailalert=true',
       'https://www.microbiologyresearch.org/content/journal/ijsem/10.1099/ijsem.0.006399?emailalert=true'
       ]

#Function to scrape headlines using Selenium
def scrape_with_selenium(url, counter):
    options = Options()
    options.headless = False  # Set to True for headless mode
    driver = webdriver.Chrome(options=options)

    #Navigate to the webpage
    driver.get(url)

    #Interact with the webpage using Selenium
    # Example: Click on a button that loads more articles
    #load_more_button = driver.find_element_by_css_selector('.load-more-button')
    #load_more_button.click()

    #Allow time for dynamic content to load (you may need to use WebDriverWait for more robust waiting)
    time.sleep(3)

    #Extract and print headlines after loading more content
    #headlines = driver.find_elements_by_css_selector('.card h3')
    #for headline in headlines:
       #print(headline.text)
    #print('test message')  
    #print(dir(driver))
    for element in driver.find_elements(By.CLASS_NAME, "item-meta-data__item-title"):
        #print(element.text)
        title = element.text
        print(title)
    #for element in driver.find_elements(By.CLASS_NAME, "author-footnote-below-abstract"): #finds all footnotes
    for element in driver.find_elements(By.ID, "FN1"): #retrieves just footnote 1
        #print(element.text)
        footnote = element.text
        #print(footnote)
    #print(driver.page_source)
    #print(title.text)
    #print(note.text)
    for element in driver.find_elements(By.CSS_SELECTOR, "div.tl-main-part.title"): #finds section headers
        #print(element.text)
        counter += 1
        section = element.text
        #print(section)
        if "Description of" in section: 
            #print('found', section)  
            #snumber = 's' + str(counter - 4) + '/p[3]'
            snumber = 's' + str(counter - 4)
            print('snumber is', snumber)
            for element in driver.find_elements(By.ID, snumber):
                description = element.text
                #print('description text is', description)
    
    #for element in driver.find_elements(By.LINK_TEXT, "Decription of"): 
        #print('text search', element.text)
    
    return title, footnote, description
    #Close the browser window
    driver.quit()

#Scrape headlines using Selenium
pub_df = pd.DataFrame(columns=['PublishedName', 'Accessions', 'Strains','URL'])
pd.set_option('display.max_columns', None)
for url in urls:
    counter = 1
    strains = []
    accessions = []
    description = None
    scrape_with_selenium(url, counter)
    #scrape_with_beautifulsoup(url)
    options = Options()
    options.headless = False  # Set to True for headless mode
    driver = webdriver.Chrome(options=options)

    #Navigate to the webpage
    driver.get(url)

    #Allow time for dynamic content to load (you may need to use WebDriverWait for more robust waiting)
    time.sleep(3)
    
    for element in driver.find_elements(By.CSS_SELECTOR, "div.tl-main-part.title"): #finds section headers
        #print(element.text)
        counter += 1
        description = element.text
        print(description)
        if "Description of" in description: 
            print('found', description)  
            #snumber = 's' + str(counter - 4) + '/p[3]'
            snumber = 's' + str(counter - 4)
            print('snumber is', snumber)
            for element in driver.find_elements(By.ID, snumber):
                description = element.text
                #print(description)
        
                #find the organism names    
                match = [r'(\S+\s+){2}(?=sp. nov.)', r'(\S+\s+){2}(?=nom. nov.)']
                regex = re.compile(r'\b(' + '|'.join(match) + r')\b')
                #orgname = [m.group() for m in regex.search(description)]
                orgname = regex.search(description).group()
                print('orgname', orgname)

                #find the accessions
                pattern = [r'[A-Z]{2}\d{6}', r'[A-Z]{4}\d{8}', r'([A-Z]+)(_[A-Z]+)\d{6}', r'[A-Z]{6}\d{9}']
                regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')
                if description is not None:
                    accessions = [m.group() for m in regex.finditer(description)]
                    print('accessions', accessions)
    
                #find the strains
                #strainpattern = [r'(?<=type strain).*'] 
                strainpattern = [r'(?<=type strain).*?(?=\))']
                regex = re.compile(r'\b(' + '|'.join(strainpattern) + r')\b')
                if description is not None:
                    strains = [m.group() for m in regex.finditer(description)]
                    print('strain names', strains)
    
                #load data into pandas dataframe
                row_data = [orgname, accessions, strains, url]
                length = len(pub_df)
                pub_df.loc[length] = row_data
            print('BREAK')
    
#Close the browser window
    driver.quit()    

