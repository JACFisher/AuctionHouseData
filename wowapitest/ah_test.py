# bdf    :
#   region    : us
#   namespace : dynamic-us
#   locale    : en_US
#   id        : 1280
# alternate ids  :  74 96 156 1068 1259 1267 1276 1280 1567
#
#
# TODO: error logging
# TODO: do not search for the name each time!  do it ONCE per item, maybe later in process?

import datetime
import json
import requests

# global variables:

token_url_by_region = \
    {
        "us": "https://us.battle.net/oauth/token",
        "eu": "https://eu.battle.net/oauth/token",
    }
api_url_by_region = \
    {
        "us": "https://us.api.blizzard.com/data/wow/",
        "eu": "https://eu.api.blizzard.com/data/wow/",
    }
url_pieces = \
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
error_codes = [404]  # expand this list


class DataScraper(object):

    def __init__(self, config_file="config.json", filename=None):
        if filename is None:
            cur_time = datetime.datetime.now().timestamp()
            self.filename = str(cur_time) + ".json"
        else:
            self.filename = filename
        # the following block is handled with load_config:
        self.region = None
        self.token_data = None
        self.realm_id_list = None
        self.locale = None
        self.load_config(config_file)
        # end load_config block
        self.token = None

    def load_config(self, config):
        with open(config, 'r') as openfile:
            config_json = json.load(openfile)
            openfile.close()
        self.token_data = config_json["token_data"]
        self.realm_id_list = config_json["realm_id"]
        if type(self.realm_id_list) is not list:
            self.realm_id_list = [self.realm_id_list]  # big brain
        self.region = config_json["region"]
        self.locale = config_json["locale"]

    def fetch_token(self):
        url = token_url_by_region[self.region]
        token_post = requests.post(url, self.token_data)
        token_json = json.loads(token_post.text)
        self.token = token_json["access_token"]

    def fetch_ah_data(self) -> dict:
        # try each realm id until we get one that doesn't error
        this_attempt = None
        for realm_id in self.realm_id_list:
            ah_url = self.build_url(url_type="auction", data=realm_id)
            this_attempt = requests.get(ah_url)
            if this_attempt.status_code not in error_codes:
                break
        if this_attempt.status_code in error_codes:
            exit(1)  # handle error logging instead
        else:
            return json.loads(this_attempt.text)

    def merge_item_names(self, cleaned_data):
        merged_data = {}
        for item_id in cleaned_data.keys():
            item_url = self.build_url(url_type="item", data=item_id)
            this_item = requests.get(item_url)
            if this_item.status_code not in error_codes:
                item_data = json.loads(this_item.text)
                item_name = item_data["name"]
            else:
                item_name = "UNKNOWN"
            auction_data = cleaned_data.get(item_id)
            auction_data.update({"name": item_name})
            merged_data.update({item_id: auction_data})
        return merged_data

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

    def main(self):
        self.fetch_token()
        auction_data = self.fetch_ah_data()
        cleaned_data = clean_auction_data(auction_data)
        final_data = self.merge_item_names(cleaned_data)
        with open(self.filename, 'w') as wf:
            json.dump(final_data, wf, indent=4, sort_keys=True)


def clean_auction_data(auction_data) -> dict:
    auction_list = auction_data["auctions"]
    cleaned_data = {}
    for auction in auction_list:
        item_id = auction["item"]["id"]
        possible_keys = ["quantity", "buyout", "unit_price"]
        temp_dict = {}
        for key in possible_keys:
            if key in auction:
                temp_dict.update({key: auction[key]})
            else:
                temp_dict.update({key: "NONE"})
        cleaned_data.update({item_id: temp_dict})
    return cleaned_data


if __name__ == "__main__":
    ds = DataScraper("my_config.json")
    ds.main()
