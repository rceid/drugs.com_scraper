#!/usr/bin/env bash

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
#CUTOFF_DATE = date(2017, 1, 31)
TSV_FILE = "./data/data.tsv"
HEADER = ["drugName", "condition", "review", "rating", "date", "usefulCount"]

def iterate_alphabet(alphabet, tsv_writer):
    #index into alphabet to start at new letter A: idx 0 || Z: idx: 26 || 0-9: idx 26
    for letter in alphabet:
        begin = datetime.now()
        url = ROOT + letter['href']
        print("At URL:\n", url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        sub_letters = soup.find("ul", attrs={"class":"ddc-paging"}).find_all("a")
        for sub in sub_letters:
            sub_url = ROOT + sub['href']
            logging.info("At letter url {} at {}:{}".format(sub_url,datetime.now().time().hour, datetime.now().time().minute))
            crawl_reviews(sub_url, tsv_writer)
        logging.info("Time {} took: {}".format(url, datetime.now() - begin))

def crawl_reviews(url, tsv_writer):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    drugs = soup.find('ul', attrs={'class': 'ddc-list-column-2'}) #get all drug urls
    if not drugs:
        drugs = soup.find('ul', attrs={'class': 'ddc-list-unstyled'}) #get all drug urls
    links = [ROOT + drug['href'] for drug in drugs.find_all('a')]
    pages = [BeautifulSoup(requests.get(link).text, 'html.parser') for link in links]
    drug_names = [page.find("h1").text for page in pages]
    reviews = [page.find('ul', attrs={'class': 'more-resources-list-general'}) for page in pages]    
    drug_revs = dict(zip(drug_names, reviews))
    drug_revs = {k:v for k, v in drug_revs.items() if v != None} #some links come out as None
    drug_revs = {drug: ROOT + rev.find('a')['href'] for drug, review in drug_revs.items() for rev in review.children if not isinstance(rev, str) and "Review" in rev.text}
    list(map(lambda drug_link: scrape_review(drug_link, tsv_writer), drug_revs.items())) #execute the scrape

def scrape_review(drug_link, tsv_writer):
    drug, link = drug_link
    sort = "?sort_reviews=most_recent"
    page = 1
    while True:
        if page == 1:
            url = link+sort
        else:
            url = link+sort+"&page="+str(page)
        r = requests.get(url)
        if r.url != url:
            break
        soup = BeautifulSoup(r.text, 'html.parser')
        reviews = soup.find_all('div', attrs={'class':'ddc-comment'})
        break_out = reviews_to_tsv(drug, reviews, tsv_writer, url, page)
        if break_out:
            break
        page += 1

def reviews_to_tsv(drug_name, reviews, tsv_writer, url, page):
    for review in reviews:
        date_ = review.find('span', attrs={'class':'comment-date'}).text
        if not check_date(date_):
            return True
        try:
            tag, review_text = [rev for rev in review.find("p", attrs={"class":"ddc-comment-content"}) if rev != "\n"]
            condition = tag.text.replace("For ", "").replace(":", "")
        except: #if there's no condition listed
            [review_text] = [rev for rev in review.find("p", attrs={"class":"ddc-comment-content"}) if rev != "\n"]
            condition = ""
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
    r = requests.get(SUB_ROOT)
    soup = BeautifulSoup(r.text, 'html.parser')
    alphabet = soup.find("span", attrs={"class":"alpha-list"}).find_all("a")
    with open(TSV_FILE, 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow(HEADER)
        iterate_alphabet(alphabet, tsv_writer)
    print("Time to process: {}".format(datetime.now() - begin))
    logging.info("Time to process: {}".format(datetime.now() - begin))
