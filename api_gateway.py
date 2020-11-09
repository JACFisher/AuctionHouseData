#############################################
#   Connects to the World of Warcraft API, providing two functions:
#       First: retrieve the name of an item given its item id.
#       Second:
#       Retrieves every auction for the server whose data
#       is listed in the config file, then cleans and returns pertinent data.
#
#   Auction data is returned in dict format, staying true to JSON standard used in API:
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
#   Example config file can be found in the sample_data folder.
#############################################

import json
import requests
from generic_util import get_timestamp, initialize_logger
# the following are only used in main :|
import os.path
import sys

# global variables:

_token_url_by_region: dict = \
    {
        "us": "https://us.battle.net/oauth/token",
        "eu": "https://eu.battle.net/oauth/token",
    }
_api_url_by_region: dict = \
    {
        "us": "https://us.api.blizzard.com/data/wow/",
        "eu": "https://eu.api.blizzard.com/data/wow/",
    }
_url_pieces: dict = \
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
_error_codes: [str] = [404]  # expand this list
_log_filename: str = "api_gateway.log"
_request_warning: str = "During {}, the following status code was received: {}"


class APIGateway(object):

    def __init__(self, config_file="config.json"):
        self.log = initialize_logger("api_gateway")
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
            self.log.ERROR("Config file not found: " + config)

    def fetch_token(self):
        url = _token_url_by_region[self.region]
        token_post = requests.post(url, self.token_data)
        token_json = json.loads(token_post.text)
        self.token = token_json["access_token"]
        self.log.info("Token received: " + self.token)

    def fetch_ah_data(self) -> dict:
        # try each realm id in list of connected realms until we get one that doesn't error
        this_attempt = None
        self.log.info('###################### AUCTION ACCESS START ######################')
        self.log.info("Reaching out to auction house api at: " + get_timestamp(human_readable=True))
        for realm_id in self.realm_id_list:
            ah_url = self.build_url(url_type="auction", data=realm_id)
            this_attempt = requests.get(ah_url)
            self.log.info("Attempted call to: " + ah_url)
            if this_attempt.status_code not in _error_codes:
                # We hit a good one
                self.log.info("Realm ID " + str(realm_id) + " returned a valid code: " + str(this_attempt.status_code))
                break
            else:
                self.log.info("Error code received: " + str(this_attempt.status_code))
        if this_attempt.status_code in _error_codes:
            self.log.warning(_request_warning.format("auction data retrieval", str(this_attempt.status_code)))
            data = {}  # return an empty dict if we never accepted data other than error codes
        else:
            data = json.loads(this_attempt.text)
        self.log.info('####################### AUCTION ACCESS END #######################')
        return data

    def fetch_item_name(self, item_id):
        if self.token_data is None:
            self.log.WARNING("Attempted to gather data without a token at: " + get_timestamp(human_readable=True))
            return {}
        else:
            item_url = self.build_url(url_type="item", data=item_id)
            self.log.info('###################### ITEM ACCESS START ######################')
            self.log.info("Reaching out to item api at: " + get_timestamp(human_readable=True))
            this_item = requests.get(item_url)
            self.log.info("Attempted call to: " + item_url)
            if this_item.status_code not in _error_codes:
                item_data = json.loads(this_item.text)
                item_name = item_data["name"]
                self.log.info("Name collected: " + item_name)
            else:
                self.log.WARNING("Received error code: " + str(this_item.status_code))
                item_name = "UNKNOWN"
            self.log.info('####################### ITEM ACCESS END #######################')
            return item_name

    def build_url(self, url_type, data) -> str:
        url = _api_url_by_region[self.region]
        url += _url_pieces[url_type]["before_id"]
        url += str(data)
        url += _url_pieces[url_type]["before_region"]
        url += self.region
        url += _url_pieces[url_type]["before_locale"]
        url += self.locale
        url += _url_pieces[url_type]["before_token"]
        url += self.token
        return url

    def gather_clean_data(self) -> dict:
        if self.token_data is None:
            self.log.WARNING("Attempted to gather data without a token at: " + get_timestamp(human_readable=True))
            return {}
        else:
            self.fetch_token()
            auction_data = self.fetch_ah_data()
            clean_data = clean_auction_data(auction_data)
            return clean_data


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


if __name__ == "__main__":
    # In general, should not be called directly, main method exists only to demonstrate use
    # accepts the filename as the first command line arg or defaults to my_config.json
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        filename = "my_config.json"
    if os.path.isfile(filename):
        ag = APIGateway(config_file=filename)
        cleaned_data = ag.gather_clean_data()
        data_outfile = "sample." + get_timestamp(human_readable=False) + ".json"
        with open(data_outfile, 'w') as wf:
            json.dump(cleaned_data, wf, indent=4, sort_keys=True)
            wf.close()

