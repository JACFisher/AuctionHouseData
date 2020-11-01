# ###########################################
#
#   Connects to the World of Warcraft auction house API, retrieves every auction for the server whose data
#   is listed in the config file, then cleans and returns the data.
#
#   Data is returned in dict format, staying true to JSON standard used in API.  Format:
#   {
#       <item_id>:
#           {
#               "buyout" : <buyout_price>
#               "quantity" : <quantity>
#               "unit_price" : <unit_price>
#           },
#       <item_id>:
#           {
#               ...
#           },
#       ...
#   }
#
#   Example can be found in the sample_data folder.
#
#   Note: this class contains methods to find each item name and append it to the aforementioned data.
#   This is not advised!  Each name takes one individual call to the server, which both takes a substantial
#   time investment and runs over the allotted calls for one client (slowing down the auction connections as well).
#
#############################################
# TODO: do not search for the name each time!  do it ONCE per item, maybe later in process?

import datetime
import json
import requests
import logging
# the following are only used in main :|
import os.path
import sys

# global variables:

token_url_by_region: dict = \
    {
        "us": "https://us.battle.net/oauth/token",
        "eu": "https://eu.battle.net/oauth/token",
    }
api_url_by_region: dict = \
    {
        "us": "https://us.api.blizzard.com/data/wow/",
        "eu": "https://eu.api.blizzard.com/data/wow/",
    }
url_pieces: dict = \
    {
        "auction":
            {
                "before_id": "connected-realm/",
                "before_region": "/auctions?namespace=dynamic-",
                "before_locale": "&locale=",
                "before_token": "&access_token="
            },
        "item":
            {
                "before_id": "item/",
                "before_region": "?namespace=static-",
                "before_locale": "&locale=",
                "before_token": "&access_token="
            }
    }
error_codes: [str] = [404]  # expand this list
log_filename: str = "auction_retriever.log"
request_warning: str = "During {}, the following status code was received: {}"


class AuctionRetriever(object):

    def __init__(self, config_file="config.json", source="program process"):
        initialize_logger(source)
        # the following block is handled with load_config:
        self.region = None
        self.token_data = None
        self.realm_id_list = None
        self.locale = None
        self.load_config(config_file)
        # end load_config block
        self.token = None

    def load_config(self, config):
        if os.path.isfile(config):
            with open(config, 'r') as openfile:
                config_json = json.load(openfile)
                openfile.close()
            self.token_data = config_json["token_data"]
            self.realm_id_list = config_json["realm_id"]
            if type(self.realm_id_list) is not list:
                self.realm_id_list = [self.realm_id_list]  # big brain
            self.region = config_json["region"]
            self.locale = config_json["locale"]
        else:
            logging.ERROR("Config file not found: " + config)

    def fetch_token(self):
        url = token_url_by_region[self.region]
        token_post = requests.post(url, self.token_data)
        token_json = json.loads(token_post.text)
        self.token = token_json["access_token"]
        logging.info("Token received: " + self.token)

    def fetch_ah_data(self) -> dict:
        # try each realm id in list of connected realms until we get one that doesn't error
        this_attempt = None
        logging.info('###################### AUCTION ACCESS START ######################')
        logging.info("Reaching out to auction house api at: " + get_timestamp(human_readable=True))
        for realm_id in self.realm_id_list:
            ah_url = self.build_url(url_type="auction", data=realm_id)
            this_attempt = requests.get(ah_url)
            logging.info("Attempted call to: " + ah_url)
            if this_attempt.status_code not in error_codes:
                # We hit a good one
                logging.info("Realm ID " + str(realm_id) + " returned a valid code: " + str(this_attempt.status_code))
                break
            else:
                logging.info("Error code received: " + str(this_attempt.status_code))
        if this_attempt.status_code in error_codes:
            logging.warning(request_warning.format("auction data retrieval", str(this_attempt.status_code)))
            data = {}  # return an empty dict if we never accepted data other than error codes
        else:
            data = json.loads(this_attempt.text)
        logging.info('####################### AUCTION ACCESS END #######################')
        return data

    def merge_item_names(self, data):
        merged_data = {}
        for item_id in data.keys():
            item_name = self.fetch_item_name(item_id)
            auction_data = data.get(item_id)
            auction_data.update({"name": item_name})
            merged_data.update({item_id: auction_data})
        return merged_data

    # DEPRECIATED - USING WEB SCRAPING
    def fetch_item_name(self, item_id):
        item_url = self.build_url(url_type="item", data=item_id)
        logging.info('###################### ITEM ACCESS START ######################')
        logging.info("Reaching out to item api at: " + get_timestamp(human_readable=True))
        this_item = requests.get(item_url)
        logging.info("Attempted call to: " + item_url)
        if this_item.status_code not in error_codes:
            item_data = json.loads(this_item.text)
            item_name = item_data["name"]
            logging.info("Name collected: " + item_name)
        else:
            logging.WARNING("Received error code: " + str(this_item.status_code))
            item_name = "UNKNOWN"
        logging.info('####################### ITEM ACCESS END #######################')
        return item_name

    def build_url(self, url_type, data) -> str:
        url = api_url_by_region[self.region]
        url += url_pieces[url_type]["before_id"]
        url += str(data)
        url += url_pieces[url_type]["before_region"]
        url += self.region
        url += url_pieces[url_type]["before_locale"]
        url += self.locale
        url += url_pieces[url_type]["before_token"]
        url += self.token
        return url

    def gather_data(self) -> dict:
        if self.token_data is None:
            logging.WARNING("Attempted to gather data without a token at: " + get_timestamp(human_readable=True))
            return {}
        else:
            self.fetch_token()
            auction_data = self.fetch_ah_data()
            clean_data = clean_auction_data(auction_data)
            return clean_data

    # DEPRECIATED - USING WEB SCRAPING
    def merge_item_names(self, data):
        merged_data = {}
        for item_id in data.keys():
            item_name = self.fetch_item_name(item_id)
            auction_data = data.get(item_id)
            auction_data.update({"name": item_name})
            merged_data.update({item_id: auction_data})
        return merged_data


def clean_auction_data(auction_data) -> dict:
    auction_list = auction_data["auctions"]
    clean_data = {}
    for auction in auction_list:
        item_id = auction["item"]["id"]
        possible_keys = ["quantity", "buyout", "unit_price"]
        temp_dict = {}
        for key in possible_keys:
            if key in auction:
                temp_dict.update({key: auction[key]})
            else:
                temp_dict.update({key: "NONE"})
        clean_data.update({item_id: temp_dict})
    return clean_data


def initialize_logger(source):
    logging.basicConfig(filename=log_filename, encoding='utf-8', level=logging.DEBUG)
    time = get_timestamp(human_readable=True)
    logging.info('**************************************************')
    logging.info("Process started at: " + time)
    logging.info("Process called by: " + source)


def get_timestamp(human_readable=False) -> str:
    cur_time = datetime.datetime.now().timestamp()
    if human_readable:
        human_readable = datetime.datetime.fromtimestamp(cur_time).isoformat()
        return human_readable
    else:
        return str(cur_time)


if __name__ == "__main__":
    # In general, should not be called directly, main method exists only to demonstrate use
    # accepts the filename as the first command line arg or defaults to my_config.json
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        filename = "my_config.json"
    if os.path.isfile(filename):
        ar = AuctionRetriever(config_file=filename, source="main method")
        cleaned_data = ar.gather_data()
        data_outfile = "sample." + get_timestamp() + ".json"
        with open(data_outfile, 'w') as wf:
            json.dump(cleaned_data, wf, indent=4, sort_keys=True)
            wf.close()
    else:
        initialize_logger(source="main method")
        logging.error("Config file not found: " + filename)
    logging.info("Process ended at: " + get_timestamp(human_readable=True))

