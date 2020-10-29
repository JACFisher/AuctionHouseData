# client : 9651ae306528449bb1a90dc58c285fcb
# secret : sUlWdzTpoy6E1DgY8D5zB92xfzYtoRHK
# bdf    :
#   region    : us
#   namespace : dynamic-us
#   locale    : en_US
#   id        : 1280
# alternate ids  :  74 96 156 1068 1259 1267 1276 1280 1567

#    lav_url = "https://us.api.blizzard.com/profile/wow/character/black-dragonflight/lav/" \
#              + "equipment?namespace=profile-us&locale=en_US&access_token="
#     z = requests.get(self.lav_url + self.access_token)
#     print(z.text)


import requests
import json


class Testies(object):

    token = None;
    config_json = None;
    filename = "help.txt"

    access_token = None

    def load_config(self, config="config.json"):
        with open(config, 'r') as openfile:
            self.config_json = json.load(openfile)

    def get_token(self):
        if self.config_json is not None:
            token_url = self.config_json["token_url"]
            token_data = self.config_json["token_data"]
            token_post = requests.post(token_url, token_data)
            token_json = json.loads(token_post.text)
            self.token = token_json["access_token"]
        else:
            pass

    def fetch_data(self, url, data=""):
        pass

    def main(self):
        self.load_config()
        self.get_token()
        print(self.token)
        # x = requests.post(self.token_url, self.data)
        # json_in = json.loads(x.text)
        # self.access_token=json_in["access_token"]
        # y = requests.get(self.auction_url + self.access_token)
        # json_in = json.loads(y.text)
        # auctions = json_in["auctions"]
        # keys = list(auctions.keys())
        # print(keys)
        # with open(self.filename, 'w') as wf:
        #    json.dump(auctions, wf, indent=4, sort_keys=True)


if __name__ == "__main__":
    t = Testies()
    t.main()







