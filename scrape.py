#!/usr/bin/env bash

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import logging
import csv
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import requests
from datetime import datetime, date
import calendar

ROOT = "https://www.drugs.com/drug_information.html"
CUTOFF_DATE = date(2017, 1, 31)

def get_driver(options):
    driver = webdriver.Chrome('./webdriver/pc/chromedriver.exe', options=options)
    driver.get(ROOT)
    sleep(1)
    driver.maximize_window()
    return driver

def back_home(driver):
    driver.get(ROOT)
    driver.execute_script("window.scrollTo(0, 250)")

def crawl_reviews(url):
    print("crawler")
    #url = "https://www.drugs.com/alpha/ab.html"
    prefix = 'https://www.drugs.com'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    drugs = soup.find('ul', attrs={'class': 'ddc-list-column-2'})
    links = [prefix + drug['href'] for drug in drugs.find_all('a')]
    pages = [BeautifulSoup(requests.get(link).text, 'html.parser') for link in links]
    reviews = [page.find('ul', attrs={'class': 'more-resources-list-general'}) for page in pages]
    reviews = list(filter(None, review_links)) #some links come out as None
    review_links = [prefix + rev.find('a')['href'] for review in review_links for rev in review.children if not isinstance(rev, str) and "Review" in rev.text]
    list(map(lambda link: scrape_review(link), review_links)) #execute the scrape

def scrape_review(link):
    sort = "?sort_reviews=most_recent"
    page = 1
    while True:
        if page == 1:
            url = link+sort
        else:
            url = link+sort+"page="+page
        try:
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            reviews = soup.find_all('div', attrs={'class':'ddc-comment'})
            reviews_to_csv(reviews)
        except: #if page doesn't exist
            break
        i += 1

def review_to_csv(reviews):
    for review in reviews:
        date_ = review.find('span', attrs={'class':'comment-date'}).text
        month, day, yr = date_.replace(",", "").split(" ")
        if int(yr) <= CUTOFF_DATE.year -1 : #quick check for year to save time
            pass
        int_month = datetime.strptime(month, "%B").month
        int_yr, int_day = int(yr), int(day)
        if int_yr == CUTOFF_DATE.year and int_month < CUTOFF_DATE.month: #same yr, earlier month
            break
        if int_yr == CUTOFF_date.year and int_month == CUTOFF_DATE.month and int_day <= CUTOFF_DATE.day:
            break
        



    return None




def iterate_alphabet(driver):
    driver.execute_script("window.scrollTo(0, 250)") 
    letters_path = "/html/body[@class='page-section-drugs page-doctype-index page-drug-information-html']/main[@id='container']/div[@id='contentWrap']/div[@id='content']/div[@class='contentBox']/ul[@class='ddc-paging']/li[{}]/a"
    for alpha_index in range(1, 28):
        letter = driver.find_element_by_xpath(letters_path.format(alpha_index))
        sleep(1)
        letter.click()
        sub_content = "/html/body[@class='page-section-drugs page-doctype-list page-alpha-a-html']/main[@id='container']/div[@id='contentWrap']/div[@id='content']/div[@class='contentBox']/div[@class='ddc-box ddc-mgb-2 paging-list-wrap']/ul[@class='ddc-paging']/li[{}]/span[@id='letter-{}']"
        letter1 = chr(ord('`')+alpha_index)
        for alpha_index2 in range(1,5):
            letter2 =  chr(ord('`')+alpha_index2)
            id_ = "letter-{}{}".format(letter1, letter2)
            print(id_)
            sleep(2)
            driver.find_element_by_id(id_).click()
            current_url = driver.current_url
            crawl_reviews(driver, current_url)

        back_home(driver)




class Bot:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = get_driver(options)
    
 

if __name__ == "__main__":
    logging.basicConfig(filename="./data/log.txt", level=logging.INFO)
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = get_driver(options)
    iterate_alphabet(driver)
