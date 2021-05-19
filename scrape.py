#!/usr/bin/env bash

'''
This script was created to scrape the Drugs.com website for user reviews using 
BeautifulSoup4. 
See if __name__ == "__main__" for the code launcher. The command line argument, 
CUTOFF_LOSS specifies the date to to which the code will scrape reviews, going
backwards from the present.
1) The scraper first obtains a list of all drugs by their first letter, crawls each
letter at a time, then finally crawls each subletter to find and scrape drugs reviews.
An example crawling sequence would be B->Ba (scrape) -> Bb (scrape) etc.
2) The scraped data is then written to a tsv file corresponding to the first letter 
of the drug.
'''

import os
import sys
from time import sleep
import logging
import csv
from bs4 import BeautifulSoup
import requests
from datetime import datetime, date
import urllib3
urllib3.disable_warnings()


ROOT = "https://www.drugs.com"
SUB_ROOT = 'https://www.drugs.com/drug_information.html'
TSV_FILE = "./data/{}_data.tsv"
HEADER = ["drugName", "condition", "review", "rating", "date", "usefulCount"]

def try_request(url):
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        print("connection refused, limit probably reached. Sleeping 15 secs then retrying")
        sleep(15)
        r = requests.get(url)
        print("Request up and running")
    return r

def iterate_alphabet(alphabet):
    for idx, letter in enumerate(alphabet):
        with open(TSV_FILE.format(letter.text.upper()), 'wt') as out_file:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow(HEADER)
            begin = datetime.now()
            url = ROOT + letter['href']
            print("At URL:\n", url)
            r = try_request(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            [list_class] = ["ddc-paging" if idx != len(alphabet)-1 else "ddc-list-column-2"]
            sub_letters = soup.find("ul", attrs={"class":list_class}).find_all("a")
            for sub_idx, sub in enumerate(sub_letters):
                sub_url = ROOT + sub['href']
                logging.info("At letter url {} at {}:{}".format(sub_url,datetime.now().time().hour, datetime.now().time().minute))
                if idx == len(alphabet)-1: #if 0-9 category
                    crawl_reviews(sub_url, tsv_writer, last_cat=True)
                crawl_reviews(sub_url, tsv_writer)
        logging.info("Time {} took: {}".format(url, datetime.now() - begin))

def crawl_reviews(url, tsv_writer, last_cat=False):
    if not last_cat:
        r = try_request(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        drugs = soup.find('ul', attrs={'class': 'ddc-list-column-2'}) #get all drug urls
        if not drugs:
            drugs = soup.find('ul', attrs={'class': 'ddc-list-unstyled'}) #get all drug urls
        links = [ROOT + drug['href'] for drug in drugs.find_all('a')]
    else:
        links = [url]
        print("Links:\n", links)
    pages = [BeautifulSoup(try_request(link).text, 'html.parser') for link in links]
    drug_names = [page.find("h1").text for page in pages]
    reviews = [page.find('ul', attrs={'class': 'more-resources-list-general'}) for page in pages]    
    drug_revs = dict(zip(drug_names, reviews))
    drug_revs = {k:v for k, v in drug_revs.items() if v != None} #some links come out as None
    drug_revs = {drug: ROOT + rev.find('a')['href'] for drug, review in drug_revs.items() for rev in review.children if not isinstance(rev, str) and "Review" in rev.text}
    list(map(lambda drug_link: scrape_review(drug_link, tsv_writer), drug_revs.items())) #execute the scrape

def by_condition(drug_link):
    drug, link = drug_link
    r = try_request(link)
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        conditions = soup.find("select", attrs={"name":"condSelect"}).find_all("option")
        condition_dict = {condition.text.split(" (")[0] : ROOT+condition['value'] for condition in conditions if not "All conditions" in condition.text}
    except:
        condition = soup.find("h1").text.split(" to treat ")[-1]
        condition_dict = {condition:link}

    return drug, condition_dict
    
def scrape_review(drug_link, tsv_writer):
    drug, condition_dict = by_condition(drug_link)
    sort = "?sort_reviews=most_recent"
    page = 1
    for condition, link in condition_dict.items():
        while True:
            if page == 1:
                url = link+sort
            else:
                url = link+sort+"&page="+str(page)
            r = try_request(url)
            if r.url != url: #if the page doesn't exist
                break
            soup = BeautifulSoup(r.text, 'html.parser')
            reviews = soup.find_all('div', attrs={'class':'ddc-comment'})
            break_out = reviews_to_tsv(drug, condition, reviews, tsv_writer, url, page)
            if break_out: #if the date is before cutoff
                break
            page += 1

def reviews_to_tsv(drug_name, condition, reviews, tsv_writer, url, page):
    for review in reviews:
        date_ = review.find('span', attrs={'class':'comment-date'}).text
        if not check_date(date_):
            return True
        try:
            _, review_text = [rev for rev in review.find("p", attrs={"class":"ddc-comment-content"}) if rev != "\n"]
        except: #if there's no condition listed
            [review_text] = [rev for rev in review.find("p", attrs={"class":"ddc-comment-content"}) if rev != "\n"]
        review_text = review_text.strip().strip('“').strip('”').replace("\r\n", " ").replace("\n", " ")
        try:
            rating = int(review.find("div", attrs={'class':"ddc-mgb-2"}).find("b").text)
        except:
            rating = "" #some reviews missing rating
        usefulness = int(review.find_all("span")[-2].text.replace("\n", ""))
        entry = [drug_name, condition, review_text, rating, date_, usefulness]
        tsv_writer.writerow(entry)

def check_date(date_str):
    month, day, yr = date_str.replace(",", "").split(" ")
    int_yr, int_day = int(yr), int(day)
    if int_yr <= CUTOFF_DATE.year -1 : #quick check for year to save time
        return False
    int_month = datetime.strptime(month, "%B").month
    if int_yr == CUTOFF_DATE.year and int_month < CUTOFF_DATE.month: #same yr, earlier month
        return False
    if int_yr == CUTOFF_DATE.year and int_month == CUTOFF_DATE.month and int_day <= CUTOFF_DATE.day: #check to the day
        return False
    return True

def parse_date(date_str):
    '''
    date must come in a YYY/MM//DD format
    '''
    assert len(date_str) == 10
    yr, mo, day = [int(unit) for unit in date_str.split("/")]
    return date(yr, mo, day)

def try_date_arg(date_arg):
    try:
        return parse_date(date_arg)
    except:
        print("{} is an invalid input, please enter date in YYYY/MM/DD format.".\
              format(date_arg))
        sys.exit()

if __name__ == "__main__":
    CUTOFF_DATE = try_date_arg(sys.argv[1])
    begin = datetime.now()
    logging.basicConfig(filename="./data/log.txt", level=logging.INFO)
    r = try_request(SUB_ROOT)
    soup = BeautifulSoup(r.text, 'html.parser')
    alphabet = soup.find("span", attrs={"class":"alpha-list"}).find_all("a")
    iterate_alphabet(alphabet)
    print("Time to process: {}".format(datetime.now() - begin))
    logging.info("Time to process: {}".format(datetime.now() - begin))
