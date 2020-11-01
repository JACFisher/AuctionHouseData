# https://www.wowhead.com/item=37012/the-horsemans-reins
# https://www.wowhead.com/item=37012

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re

known_valid_url: str = "https://www.wowhead.com/item=37012/the-horsemans-reins"
item_url: str = "https://www.wowhead.com/item="
invalid_url: str = "https://www.wowhead.com/items?notFound="
hdr: dict = {'User-Agent': 'Mozilla/5.0'}


class ItemNameRetriever(object):

    def __init__(self):
        pass

    def main(self):
        fetch_url(1)


def found_valid_item(url) -> bool:
    return "notFound" not in url


def fetch_url(item_id) -> str:
    site = "https://www.wowhead.com/item=785/mageroyal"
    req = Request(site, headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, features="html.parser")
    script = soup.findAll("script")
    if script:
        for line in script:
            print(line)


if __name__ == "__main__":
    inr = ItemNameRetriever()
    inr.main()