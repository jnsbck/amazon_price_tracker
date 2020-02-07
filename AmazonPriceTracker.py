import numpy as np
import matplotlib.pyplot as plt # for plotting price data
import pandas as pd
from pandas.errors import EmptyDataError # error produced if empty csv if parsed

from bs4 import BeautifulSoup
import requests # fetches html content of a website, instead of urllib2 previously
from urllib.request import HTTPError # for catching timeout for website response

import time # for sleep function
from datetime import datetime # for timestamp

import os # for creation of directories



class AmazonPriceTracker:
    
    def __init__(self, tracker_name="tracker"):
        self.items = {"nicknames": [], "names": [], "asins": [], "urls": []}
        self.name = tracker_name
        self.PATH = "./" + self.name + "/"
        try:
            os.mkdir(str(self.name))
        except FileExistsError:
            print("This tracker already exists. Using the existing one instead.")
        
        self.price_history = {}
        self.__retrieve_items()
        
        DateTime = ["year", "month", "day", "hour", "minute"]
        self.price_history = pd.DataFrame(columns=DateTime+self.items["nicknames"])
        
        self.__retrieve_price_hist()
        self.latest_prices = self.price_history.tail(1)
        
    def __webpage2html(self, URL, parser="html.parser"):
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        }
        res = requests.get(URL, headers=headers)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, 'html.parser')
        return soup

     
    def add_item(self, URL, nickname):
        if "amazon" not in URL:
            print("This is not a valid amazon url.")
        else:
            ASIN = URL.split("/")[4]
            URL = "/".join(URL.split("/")[:5])
            if ASIN not in self.items["asins"]:
                print("Adding item to list of tracked items.")
                try:
                    soup = self.__webpage2html(URL)

                    # extract name
                    for element in soup.find_all("span"):
                        if "productTitle" in str(element):
                            title_containing_str = str(element)
                            break
                    title_containing_str_start = title_containing_str.find(">")+1
                    title_containing_str_end = title_containing_str.find("</")
                    title_raw = title_containing_str[title_containing_str_start:title_containing_str_end]
                    title = title_raw.replace("\n", "").replace("  ", "")

                    # save title and URL to txt
                    f = open(self.PATH + "tracked_items.txt","a", newline="\n")
                    if title not in self.items["names"]:
                        f.write(nickname + " : " + title + " : " + URL + " : " + ASIN + "\n")
                    f.close()

                    # save title and URL to dict
                    self.items["names"].append(title)
                    self.items["urls"].append(URL)
                    self.items["nicknames"].append(nickname)
                    self.items["asins"].append(ASIN)
                    print("{} was succesfully added to list of tracked items.".format(nickname))

                except HTTPError:
                    print("HTTP 503 Error, try to add item again later.")
            else:
                print("This item is already being tracked.")
            
            
    def __retrieve_items(self):
        # retrieve tracked items
        try:
            f = open(self.PATH + "tracked_items.txt", "r")
            if f.read() == "":
                print("No items are being tracked so far. \
                Please add an item to be tracked using .add_item().")
                f.close()
            else:
                f = open(self.PATH + "tracked_items.txt", "r")
                lines = f.readlines()
                for line in lines:
                    nickname, title, url, asin = line.split(" : ")
                    if asin[:-1] not in self.items["asins"]:
                        self.items["names"].append(title)
                        self.items["urls"].append(url)
                        self.items["nicknames"].append(nickname)
                        self.items["asins"].append(asin[:-1])
            f.close()
        except FileNotFoundError:
            open(self.PATH + "tracked_items.txt", "x")
    
    
    def __retrieve_price_hist(self):
        try:
            self.price_history = pd.read_csv(self.PATH + "price_history.csv")
        except FileNotFoundError:
            open(self.PATH + "price_history.csv", "x")
        except EmptyDataError:
            if len(self.items["names"]) > 0:
                print("The price history is empty so far. \
                Please fetch prices using .fetch_prices() first.")
            else:
                pass
        
        
    def wipe_database(self):
        # delete contents of files
        items = open(self.PATH + "tracked_items.txt", "w")
        items.write("")
        items.close()
        
        hist = open(self.PATH + "price_history.csv", "w")
        hist.write("")
        hist.close()
        
        
    def fetch_prices(self, URLs=None):  
        # extract price
        if URLs is None:
            URLs = self.items["urls"]
        error_status = None
        delay = 1 # delay between fetching items in s
        DateTime = ["year", "month", "day", "hour", "minute"]
        new_row = pd.DataFrame(columns=DateTime+self.items["nicknames"])
        if len(self.items["names"]) > 0:
            for n, URL in enumerate(URLs):
                try:
                    print("Fetching price for {}.".format(self.items["nicknames"][n]))
                    soup = self.__webpage2html(URL, "lxml")
                    time.sleep(delay)

                    price_str = soup.select("#priceblock_ourprice")[0].text.replace(",",".")
                    price = float(price_str[:price_str.index(".")+3])
                    item_name = self.items["nicknames"][n]
                    new_row[item_name] = [price]
                    
                except HTTPError:
                    item_name = self.items["nicknames"][n]
                    new_row[item_name] = [np.NaN]
                    print("\n A price for {} could not be fetched.".format(item_name))
                    error_status = True
        
            now = datetime.now()
            datetime_vec = now.timetuple()[0:5]
            new_row[DateTime] = datetime_vec
            new_row.index = range(self.price_history.shape[0],self.price_history.shape[0]+1)
            self.price_history = self.price_history.append(new_row, sort=False, ignore_index=True)
            self.latest_prices = self.price_history.tail(1)

            # save price history
            self.price_history.to_csv(self.PATH + "price_history.csv", index_label=False, index=False)
    
        else:
            print("There is no items to fetch a price for. Please add items using .add_item() first.")
    
        return error_status
                
        
    def remove_item(self):
        print("The items currently being tracked are: \n")
        for i in range(len(self.items["nicknames"])):
            print("[" + str(i) + "] --> " + self.items["nicknames"][i])
        Input = input("\n To remove an item from tracking enter the corresponding number.\
        \n To cancel, press 'Enter'. ")
        if Input.isdigit():
            item2delete_idx = int(Input)
            if item2delete_idx < len(self.items["nicknames"]):
                item_name = self.items["nicknames"][item2delete_idx]

                # remove from hist
                self.price_history = self.price_history.drop(item_name, axis=1)
                
                # remove from tracked items
                self.items["names"].pop(item2delete_idx)
                self.items["nicknames"].pop(item2delete_idx)
                self.items["urls"].pop(item2delete_idx)
                self.items["asins"].pop(item2delete_idx)
                
                # remove from corresponding .txt and .csv
                f_read = open(self.PATH + "tracked_items.txt", "r")
                lines = f_read.readlines()
                lines.pop(item2delete_idx)
                f_write = open(self.PATH + "tracked_items.txt", "w")
                f_write.write("".join(lines))
                f_read.close()
                f_write.close()
                
                self.price_history.to_csv(self.PATH + "price_history.csv", index_label=False)
                
                print("Item was removed.")
            else:
                print("The input does not correspond to an item.")
        elif Input == "":
            print("The action has been canceled.")
        else:
            print("The input is not valid.")
        

    def plot_prices(self, timescale="day"):
        fig = plt.figure(figsize=(10,6))
        time_axis = self.price_history[timescale]
        tracked_items = list(self.price_history.columns)[5:]
        for item in tracked_items:
            plt.plot(time_axis,self.price_history[item], "-o" , label=item)
        
        plt.legend()
        plt.grid()
        plt.xlabel(timescale + "s")
        plt.ylabel("Price in €")
        plt.show()
        
        
    def current_prices(self):
        self.fetch_prices()
        current_price = self.latest_prices
        return current_price

        
    def deploy(self):
        while True:
            _time = datetime.now().timetuple()[2:5]
            today = _time[0]
            hour = _time[1]
            minute = _time[2]
            try:
                prev_year, prev_month, prev_day, *_ = np.loadtxt(self.PATH + "price_history.csv", skiprows=1, delimiter=",")[-1]
            except TypeError:
                prev_year, prev_month, prev_day, *_ = np.loadtxt(self.PATH + "price_history.csv", skiprows=1, delimiter=",")
            except StopIteration:
                prev_year, prev_month, prev_day = -1, -1, -1
            print("Checking time...")
            if hour == 0 and (minute < 59 and minute > 0):
                if prev_day != today:
                    attempt = 1
                    URLs = np.array(self.items["urls"])
                    while attempt < 10:
                        try:
                            print("Attempt {} to fetch prices.".format(attempt))
                            status = self.fetch_prices(URLs)
                            if status == None:
                                print("Fetching was a success!")
                                print("...waiting for next fetch.")
                                break
                            else:
                                latest_prices = self.price_history.iloc[-1,5:]
                                fails = np.array(latest_prices.isna())
                                URLs = URLs[fails]
                                attempt += 1
                                nicknames_of_fails = np.array(self.items["nicknames"])[fails]
                                print("Encountered an error while fetching prices for {}. Trying again in 10 min.".format(list(nicknames_of_fails)))
                                time.sleep(10*60)
                        except HTTPError:
                            print("HTTP 503 Error, trying again in 10 minutes.")
                            attempt += 1
                            time.sleep(10*60)
                else:
                    print("Item prices have already been updated today.")
            time.sleep(59*60)
