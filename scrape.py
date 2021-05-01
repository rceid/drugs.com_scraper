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

ROOT = "https://www.drugs.com/drug_information.html"

def get_driver(options):
    driver = webdriver.Chrome('./webdriver/pc/chromedriver.exe', options=options)
    driver.get(ROOT)
    sleep(1)
    driver.maximize_window()
    return driver

def back_home(driver):
    driver.get(ROOT)
    driver.execute_script("window.scrollTo(0, 250)")

def crawl_reviews(driver, url):
    print("crawler")
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    drugs = soup.find_all('ul', attrs={'class': 'ddc-list-column-2'})

    ###stopped here. THis gets all of the links for the two letter category
    

    # i = 0
    # review_path = "/html/body[@class='page-section-drugs page-doctype-list page-alpha-ab-html']/main[@id='container']/div[@id='contentWrap']/div[@id='content']/div[@class='contentBox']/ul[@class='ddc-list-column-2']/li[{}]/a"
    # while True:
    #     i += 1
    #     driver.execute_script("window.scrollTo(0, {})".format(250+(i*10)))
    #     sleep(1)
    #     try:
    #         drug = driver.find_element_by_xpath(review_path.format(i))
    #     except:
    #         print("No drugs for this prefix")
    #         break
    #     try:
    #         drug.click()
    #         scrape_review(driver)
    #     except:
    #         print("End of list at idx {}".format(i))

def scrape_review(driver):
    print("scraper_")
    sleep(2)
    rev = "/html/body[@class='page-section-cons page-doctype-content page-cons-a-b-otic-html']/main[@id='container']/div[@id='contentWrap']/div[@id='sidebar']/div[@class='sideBox sideBoxUserReviews']/div[@class='sideBoxContent ddc-clearfix']/div[@class='ddc-rating-summary']/em/a"
    reviews= driver.find_element_by_xpath(rev)
    sleep(2)
    print('scrolling')
    driver.execute_script("arguments[0].scrollIntoView();", reviews)
    print('scrolled)')
    reviews_button.click()

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
