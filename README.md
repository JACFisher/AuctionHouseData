# AuctionHouseData
Uses the Battle.net api to gather auction data for a given World of Warcraft server and plot trends.

# The config file:
For token_data:
- client_id and client_secret are requested at:
  https://develop.battle.net/access/clients/create
    
For realm_id:
- request through api (example):
    https://eu.api.blizzard.com/data/wow/search/connected-realm?namespace=dynamic-eu&realms.name.en_US=kazzak&access_token=YOUR_TOKEN
- IMPORTANT NOTE:
    If your realm is in the list of connected realms (https://wow.gamepedia.com/Connected_Realms),
    you may find that your realm ID gives a 404 error!  In fact, for Black Dragonflight
    I had to use a list!  The numerically lower ID's tended to work more frequently - YMMV.
    ex: [id1,id2,id3]