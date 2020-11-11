from api_gateway import APIGateway
from database_gateway import DatabaseGateway
import os

class Controller(object):

    def __init__(self, api_config="config.json"):
        self.ag = APIGateway(api_config)
        self.dg = DatabaseGateway()

    def collect_and_store_data(self):
        data = self.ag.gather_clean_data()
        self.dg.connect_to_db()
        self.dg.create_tables()
        self.dg.add_auction_data(data)
        self.dg.close_connection()


if __name__ == '__main__':
    config_filepath = os.path.join(os.path.dirname(__file__), "data", "config")
    config_file = os.path.join(config_filepath, "my_config.json")
    con = Controller(config_file)
    con.collect_and_store_data()