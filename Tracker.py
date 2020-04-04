import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt # for plotting price data
# from pandas.errors import EmptyDataError # error produced if empty csv if parsed

from bs4 import BeautifulSoup
import requests # fetches html content of a website, instead of urllib2 previously
from urllib.request import HTTPError # for catching timeout for website response
from urllib.request import urlopen
from urllib.request import URLError

import time # for sleep function
from datetime import datetime # for timestamp

import os # for creation of directories
import re # for regular expressions

class Item():
    def __init__(self, nickname=None, description=None, url=None, asin=None, price=None, currency=None, last_updated=None, in_stock=None, created=None):
        self.Nickname = nickname
        self.Description = description
        self.Asin = asin
        self.Url = url
        self.Price = price
        self.Currency = currency
        self.Created = created
        self.Last_updated = last_updated
        self.In_stock = in_stock
        self.Price_log = {"timestamp": [last_updated], "price": [price]}
        self.DatetimeFormatStr = "%H:%M, %m/%d/%Y"# "(%Y, %m, %d, %H, %M)" # temporary better: "%H:%M, %m/%d/%Y"
    
    def __str__(self):
        return str({
                "Nickname": self.Nickname,
                "Description": self.Description,
                "Asin": self.Asin,
                "Url": self.Url,
                "Price": self.Price, 
                "Currency": self.Currency,
                "In_stock":self.In_stock,
                "Created": self.Created.strftime(self.DatetimeFormatStr),
                "Last_updated": self.Last_updated.strftime(self.DatetimeFormatStr)
               })
    
    def from_txt(self, file):
        with open(file, "r") as f:
            class_attrs = eval(f.readline()) # eval is always dangerous! temporary
            self.Price_log = eval(f.readline()) # eval is always dangerous! temporary
            for index, (timestamp,price) in enumerate(zip(self.Price_log["timestamp"], self.Price_log["price"])):
                self.Price_log["timestamp"][index] = datetime.strptime(timestamp, self.DatetimeFormatStr) # str neccesary because of eval()
                self.Price_log["price"][index] = float(price)
        
        self.Nickname =  class_attrs["Nickname"]
        self.Description = class_attrs["Description"]
        self.Asin = class_attrs["Asin"]
        self.Url = class_attrs["Url"]
        self.Price = float(class_attrs["Price"])
        self.Currency = class_attrs["Currency"]
        self.Created = datetime.strptime(str(class_attrs["Created"]), self.DatetimeFormatStr) # str neccesary because of eval()
        self.Last_updated = datetime.strptime(str(class_attrs["Last_updated"]), self.DatetimeFormatStr) # str neccesary because of eval()

    def __reformat_date(self, date):
        return datetime.strftime(date, self.DatetimeFormatStr)

    def to_txt(self, path="./"):
        with open(path + self.Nickname + ".txt", "w") as f:
            f.write(self.__str__() + "\n")
            price_log = self.Price_log.copy()
            price_log["timestamp"] = list(map(self.__reformat_date, price_log["timestamp"]))
            f.write(str(price_log)) # temporary solution

class Scraper():
    def __init__(self):
        self.Online = False
        
    def webpage2soup(self, url, parser="lxml"):
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, parser)
        return soup
            
    def test_connection(self, url='http://216.58.192.142'):
        try:
            urlopen(url, timeout=1)
            self.Online = True
        except URLError as err:
            self.Online = False
        return self.Online
    
    def ping_AmazonDE(self):
        return test_connection("amazon.de")


class Parser():
    def __init__(self):
        self.Template_Amazon_Url = r"(https://)*(www.)*([a-z_-]+)\.([a-z]+)/([a-z0-9-_]+)/([a-z0-9-_]+)/([a-z0-9-_]+)" # Amazon regex
        self.Template_Amazon_Description = r"(<span\s(class=\"a-size-large\"\s)*(id=\"productTitle\")(\sclass=\"a-size-large\")*>\n\s+(.+)\n\s+</span>)"
        self.Template_Amazon_Price = r"([0-9,]+)\s(.)"
        
    def __groupbytemplate(self, string, re_template):
        regex = re.compile(re_template)
        m = regex.search(string)
        return m.groups()        
        
    def find_attributes(self, html):
        attributes = {"description": "",
                      "currency": "",
                      "price": ""}
        
        # find product description
        description = self.find_description(html)
        attributes["description"] = description
        
        # find price and currency
        price, currency = self.find_price(html)
        attributes["price"] = float(price)
        attributes["currency"] = currency
           
        return attributes
    
    def parse_url(self,url):
        regex = re.compile(self.Template_Amazon_Url)
        m = regex.search(url.lower())
        url_slices = m.groups()
        
        topleveldomain = "." + url_slices[3]
        
        if url_slices[3] == "de":
            if url_slices[4] == "gp":
                asin = url_slices[6]
            else:
                asin = url_slices[5]
        elif url_slices[3] == "com":
            asin = url_slices[6]
        else:
            pass # so far only .com and .de supported
            
        return asin, topleveldomain
    
    def find_price(self, html):
        price_str = str(html.select("span#priceblock_ourprice"))
        groups = self.__groupbytemplate(price_str, self.Template_Amazon_Price)
        price = groups[0].replace(",", ".")
        currency = groups[1]
        return price, currency
    
    def find_description(self, html):
        title_str = "" # why do I have to reference this var before?
        for element in html.find_all("span"):
            if "productTitle" in str(element):
                title_str = str(element)
                break
        groups = self.__groupbytemplate(title_str, self.Template_Amazon_Description)
        description = groups[4]
        return description

class Notifier():
    def __init__(self, path="./", logfile="events"):
        self.Last_event = np.array(["timestamp", "event", "status"]) # event + timestamp
        open(path + logfile + ".log", "a")
        self.Log_path = path
        self.Logfile_name = logfile
        self.Log = ""
        
    def prompt(self, event="", end_char=" ", kind="event", status="ongoing"):
        if kind == "event":
            timestamp = datetime.now()
            print(str(timestamp) + " -- " + event, end=end_char)
            self.Last_event = np.array([timestamp, event, status])
        if kind == "response":
            print(event + "!")
            timestamp = datetime.now()
            self.Last_event[0] = timestamp
            self.Last_event[2] = event

        return timestamp, event
    
    def log(self, event="", end_char=" ", kind="event", status="ongoing"):
        timestamp, event = self.prompt(event, end_char, kind, status)
        self.Log = self.Log + str(timestamp) + " -- " + event + end_char
        with open(self.Log_path + self.Logfile_name + ".log", "a") as f:
            if kind == "event":
                f.write(str(timestamp) + " -- " + event + end_char)
            if kind == "response":
                f.write(" " + event + "!\n")

    def send_email(self):
        pass

class Tracker(Item, Scraper, Notifier, Parser):
    def __init__(self, name="default_tracker", path="./", load=False):
        self.Path = path + name + "/"
        self.Name = name
        self.Items = []
        
        Scraper.__init__(self)
        Parser.__init__(self)
        
        if load:
            Notifier.__init__(self, self.Path)
            self.load(self.Path)
        else:
            try:
                os.mkdir(self.Path)
                Notifier.__init__(self, self.Path)
                self.log(self.Name + " created.", end_char="\n", status="success")
            except FileExistsError:
                response = input("A tracker with this name already exists, do you want to load it? [Yes/No]: ")
                if response.lower()[0] == "y":
                    Notifier.__init__(self, self.Path)
                    self.load(self.Path)
                else:
                    self.log(self.Name + " initialised as blank.", end_char="\n", status="success")
                    Notifier.__init__(self, self.Path)
        
    def __asin(self, item):
        return item.Asin    
    
    def add_item(self, nickname=None, description=None, url=None, asin=None, price=None, currency=None, last_updated=None, in_stock=None, created=None, save=False):
        if asin.lower() not in list(map(self.__asin,tracker.Items)):
            self.log("Adding " + nickname + "to list of tracked items...")
            item = Item(nickname, description, url, asin, price, currency, last_updated, in_stock, created)
            self.Items.append(item)
            self.log("success", kind="response")
        
            if save:
                self.log("Saving " + nickname + "...")
                item.to_txt(self.Path)
                self.log("success", kind="response")
        else:
            self.log("ASIN matches an item that is already being tracḱed.", end_char="\n")
    
    def add_item_by_url(self, alias, url, save=False):
        self.log("Parsing " + url + "...")
        asin, _ = self.parse_url(url)
        self.log("success", kind="response")
        if asin not in list(map(self.__asin,tracker.Items)):
            self.log("Fetching webpage for " + alias + "...")
            html = self.webpage2soup(url)
            self.log("success", kind="response")
            
            self.log("Fetching attributes for " + alias + "...")
            attributes = self.find_attributes(html)
            self.log("success", kind="response")
            
            nickname = alias
            description = attributes["description"]
            price = attributes["price"]
            currency = attributes["currency"]
            created = datetime.now()
            in_stock = None # for now will be set to None. Full mechanic not implemented yet

            self.add_item(nickname, description, url, asin, price, currency, created, in_stock, created, save)
        else:
            self.log("ASIN matches an item that is already being tracḱed.", end_char="\n")
        
    def list_items(self):
        for item in self.Items:
            print(item.Nickname)
    
    def fetch_price(self, Item):
        html = self.webpage2soup(Item.Url)
        self.log("Fetching price and currency for " + Item.Nickname + "...")
        price, currency = self.find_price(html)
        self.log("success", kind="response")
        return price, currency
    
    def update_prices(self, timeb4nextfetch=0):
        now = datetime.now()
        for Item in self.Items:
            try:
                price, _ = self.fetch_price(Item)
                Item.Price = price
            except:
                Item.Price = np.nan
                self.log("failed", kind="response")
                
            Item.Last_updated = now
            Item.Price_log["timestamp"].append(now)
            Item.Price_log["price"].append(price)
            time.sleep(timeb4nextfetch)
                
    def deploy(self):
        self.log(self.Name + " has been deployed.")
        while(True):
            self.log("Pinging Amazon.de...")
            if self.test_connection(url="http://amazon.de"):
                self.log("success", kind="response")
                self.update_prices(5)
                self.log("All prices have been updated.", status="success", end_char="\n")
                self.save()
                self.history_to_csv(True)
                self.log("Waiting 12 hours for next update...", end_char="\n")
                time.sleep(60*60*12)
            else:
                self.log("failed", kind="response")
                self.log("Waiting 10min before trying again...")
                time.sleep(60*10)
                self.log("finished waiting", kind="response")
    
    def load(self, path):
        self.Path = path
        regex = re.compile(r"/([a-zA-Z0-9-_]+)/$")
        m = regex.search(path)
        self.Name = m.groups()[0]
        if len(self.Items) == 0:
            files_in_dir = [f for f in os.listdir(self.Path) if os.path.isfile(os.path.join(self.Path, f))]
            for file in files_in_dir:
                if file[-4:] == ".txt":
                    item = Item()
                    self.log("Importing "+ item.Nickname + "...")
                    item.from_txt(self.Path + file)
                    self.Items.append(item)
                    self.log("success", kind="response")
        self.log("Loading logfile...")
        with open(self.Log_path + self.Logfile_name + ".log") as f:
            self.Log = f.read()
        self.log("success", kind="response")
                    
    def save(self):
        self.log("Saving current state...")
        for item in self.Items:
            item.to_txt(self.Path)
        self.log("success", kind="response")
            
    def __reformat_date(self, date):
        return datetime.strftime(date, Item().DatetimeFormatStr)
    
    def history_to_csv(self, save=False):  
        df = pd.DataFrame({})
        self.log("Creating .csv from archived prices...")
        for item in self.Items:
            dct = {item.Nickname: []}
            timestamps, prices = item.Price_log.values()
            for timestamp, price in zip(timestamps, prices):
                dct[item.Nickname].append(price)
            df_item = pd.DataFrame(dct, index=[list(map(self.__reformat_date, timestamps))])
            df = pd.concat([df, df_item], axis=1)
        df.index.name = "timestamp"
        self.log("success", kind="response")
        if save:
            self.log("Saving price history to .csv...")
            df.to_csv(self.Path + "price_hist.csv")
            self.log("success", kind="response")
            
        return df         
