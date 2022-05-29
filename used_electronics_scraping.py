# This program scrapes second-hand electronics websites for items for sale, then store into CockroachDB SQL database

import time
import random
import logging
import os
from argparse import ArgumentParser, RawTextHelpFormatter

import psycopg2
from psycopg2.errors import SerializationFailure

from bs4 import BeautifulSoup
import urllib.request
from urllib.request import Request, urlopen


def web_scraping(url):
    ''' Takes in company retail url for specific items and finds the electronics being sold
    '''
    file = urllib.request.urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
    html_doc = file.read().decode("utf-8")
    file.close()

    links = []
    model = {}

    soup = BeautifulSoup(html_doc, 'html.parser')


    # find product name
    for link in soup.find_all('h3'):
        link =  str(link)
        if "a href=" in link:
            if link not in links:
                name = link.replace('<', '>').replace('>>', '>').split(">")
                links.append({"product name": name[-4]})


    # find product price
    spans = soup.find_all('span', {'class' : 'price-without-icon'})
    for i in range(len(spans)):
        if "CAD$" in str(spans[i]):
            price = str(spans[i]).replace("\r", "").replace("CAD", "").split('\n')
            links[i]["price"] = price[1]


    # set operating system
    for i in range(len(links)):
        links[i]["OS"] = "Windows"


    # find RAM
    descrip = []
    descriptions = str(soup).split("<")
    for i in range(len(descriptions)):
        if 'p class="description">' in descriptions[i]:
            descrip.append(descriptions[i])
            
    for i in range(len(descrip)):
        descrip[i] += links[i]["product name"]
        descrip[i] = descrip[i].replace("/", " ").split(" ")
        for j in range(len(descrip[i])):
            if "RAM" in descrip[i][j]:
                links[i]["RAM"] = descrip[i][j]

    return links


def add_product(conn):
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS laptop (productName VARCHAR, price INT, os VARCHAR, ram VARCHAR)"
        )
        cur.execute(
            "UPSERT INTO products (productName, price, os, ram) VALUES ")
        logging.debug("add_product(): status message: %s",
                      cur.statusmessage)
    conn.commit()


def print_table(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, balance FROM accounts")
        logging.debug("print_table(): status message: %s",
                      cur.statusmessage)
        rows = cur.fetchall()
        conn.commit()
        print(f"Balances at {time.asctime()}:")
        for row in rows:
            print(row)

def parse_cmdline():
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument("-v", "--verbose",
                        action="store_true", help="print debug info")

    parser.add_argument(
        "dsn",
        default=os.environ.get("DATABASE_URL"),
        nargs="?",
        help="""\
database connection string\
 (default: value of the DATABASE_URL environment variable)
            """,
    )

    opt = parser.parse_args()
    if opt.dsn is None:
        parser.error("database connection string not set")
    return opt


def main():
    opt = parse_cmdline()
    logging.basicConfig(level=logging.DEBUG if opt.verbose else logging.INFO)
    try:
        # Attempt to connect to cluster with connection string provided to
        # script. By default, this script uses the value saved to the
        # DATABASE_URL environment variable.
        # For information on supported connection string formats, see
        # https://www.cockroachlabs.com/docs/stable/connect-to-the-database.html.
        db_url = opt.dsn
        conn = psycopg2.connect(db_url)
    except Exception as e:
        logging.fatal("database connection failed")
        logging.fatal(e)
        return

    add_product(conn)
    print_table(conn)





if __name__ == "__main__":

    # Green Moolaa
    url = "https://shop.greenmoolaa.ca/Subcategory/Laptops-Netbooks/16876034"
    dict = web_scraping(url)

    print(dict)



