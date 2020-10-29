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

    client = "9651ae306528449bb1a90dc58c285fcb"
    secret = "sUlWdzTpoy6E1DgY8D5zB92xfzYtoRHK"
    data = {"client_id":client, "client_secret":secret, "grant_type":"client_credentials"}
    token_url = "https://us.battle.net/oauth/token"
    realm_id = 96
    auction_url = "https://us.api.blizzard.com/data/wow/connected-realm/" \
                  + str(realm_id) + "/auctions?namespace=dynamic-us&locale=en_US&access_token="
    filename = "help.txt"

    access_token = None

    def main(self):
        x = requests.post(self.token_url, self.data)
        json_in = json.loads(x.text)
        self.access_token=json_in["access_token"]
        y = requests.get(self.auction_url + self.access_token)
        json_in = json.loads(y.text)
        auctions = json_in["auctions"]
        # keys = list(auctions.keys())
        # print(keys)
        # with open(self.filename, 'w') as wf:
        #    json.dump(auctions, wf, indent=4, sort_keys=True)




if __name__ == "__main__":
    t = Testies()
    t.main()







