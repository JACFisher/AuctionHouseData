#######################################################################################################################
#
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
#   Requires a config file.  An example config file can be found in the sample_data folder, and more information
#   is available in the README.
#
#######################################################################################################################

import json
import requests
import generic_util as gu
import os

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
_log_filename: str = "api_gateway"


class APIGateway(object):

    def __init__(self, config_file="config.json", logger=None):
        if logger is not None:
            self.log = logger
        else:
            self.log = gu.initialize_logger("api_gateway.py")
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
            self.token_data = config_json["token_data"]
            self.realm_id_list = config_json["realm_id"]
            if type(self.realm_id_list) is not list:
                self.realm_id_list = [self.realm_id_list]  # big brain
            self.region = config_json["region"]
            self.locale = config_json["locale"]
        else:
            self.log.error("Config file not found: " + config)

    def fetch_token(self):
        url = _token_url_by_region[self.region]
        token_post = requests.post(url, self.token_data)
        token_post.close()
        token_json = json.loads(token_post.text)
        self.token = token_json["access_token"]
        self.log.info("Token received!")

    def fetch_ah_data(self) -> dict:
        # try each realm id in list of connected realms until we get one that doesn't error
        this_attempt = None
        self.log.info('###################### AUCTION ACCESS START ######################')
        self.log.info("TIME: " + gu.get_timestamp(human_readable=True))
        for realm_id in self.realm_id_list:
            ah_url = self.build_url(url_type="auction", data=realm_id)
            this_attempt = requests.get(ah_url)
            this_attempt.close()
            self.log.info("Attempted call to: " + ah_url)
            if this_attempt.status_code not in _error_codes:
                # We hit a good one
                self.log.info("Realm ID " + str(realm_id) + " returned a valid code: " + str(this_attempt.status_code))
                break
            else:
                self.log.info("Error code received: " + str(this_attempt.status_code))
        if this_attempt.status_code in _error_codes:
            self.log.warning("While retrieving auction data, the following code was received:")
            self.log.warning(str(this_attempt.status_code))
            data = {}  # return an empty dict if we never accepted data other than error codes
        else:
            data = json.loads(this_attempt.text)
        self.log.info("TIME: " + gu.get_timestamp(human_readable=True))
        self.log.info('####################### AUCTION ACCESS END #######################')
        return data

    def fetch_item_data(self, item_id) -> dict:
        if not self.check_token_status("gather item names"):
            return {}
        else:
            item_url = self.build_url(url_type="item", data=item_id)
            self.log.info('###################### ITEM ACCESS START ######################')
            self.log.info("Reaching out to item api at: " + gu.get_timestamp(human_readable=True))
            this_item = requests.get(item_url)
            this_item.close()
            self.log.info("Attempted call to: " + item_url)
            if this_item.status_code not in _error_codes:
                item_data = json.loads(this_item.text)
                item_name = item_data["name"]
                item_quality = item_data["quality"]["type"]
                self.log.info("Name collected: " + item_name)
            else:
                self.log.warning("Received error code: " + str(this_item.status_code))
                item_name = "UNKNOWN"
            self.log.info('####################### ITEM ACCESS END #######################')
            useful_item_data = {
                "name": item_name,
                "quality": item_quality
            }
            return useful_item_data

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
        if not self.check_token_status("gather auction data"):
            return {}
        else:
            self.fetch_token()
            auction_data = self.fetch_ah_data()
            clean_data = clean_auction_data(auction_data)
            return clean_data

    def check_token_status(self, message) -> bool:
        if self.token_data is None:
            self.log.warning("Attempted to {} without a token at: ".format(message))
            return False
        return True


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


#######################################################################################################################
#
#   The following exists for demonstration purposes only.
#   The true main entry point for this program is located in __main__.py
#   Relies on a file named "my_config.json" - a sample is available in the sample_config directory.
#   More information on the expected config can be found in the README
#
#######################################################################################################################


if __name__ == "__main__":
    # Writes to the auction_sample_data directory found in the data directory
    # This is where the main for database_gateway.py checks for data
    # Recreates the directory if missing
    config_filepath = os.path.join(os.path.dirname(__file__), "data", "config")
    config_filename = os.path.join(config_filepath, "my_config.json")
    sample_data_folder = os.path.join(os.path.dirname(__file__), "data", "auction_sample_data")
    if not os.path.exists(sample_data_folder):
        os.makedirs(sample_data_folder)
    if not os.path.exists(config_filepath):
        os.makedirs(config_filepath)
    if os.path.isfile(config_filename):
        ag = APIGateway(config_file=config_filename)
        cleaned_data = ag.gather_clean_data()
        data_outfile = "sample." + gu.get_timestamp(human_readable=False) + ".json"
        data_filename = os.path.join(sample_data_folder, data_outfile)
        data_filename = os.path.normpath(data_filename)
        with open(data_filename, 'w') as wf:
            json.dump(cleaned_data, wf, indent=4, sort_keys=True)
