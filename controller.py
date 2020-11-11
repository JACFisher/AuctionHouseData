from api_gateway import APIGateway
from database_gateway import DatabaseGateway
import generic_util as gu
import os


class Controller(object):

    def __init__(self, api_config="config.json"):
        self.log = gu.initialize_logger("controller.py")
        self.ag = APIGateway(api_config, self.log)
        self.dg = DatabaseGateway(self.log)

    def collect_and_store_data(self):
        self.log.info("Module (controller.py) using (api_gateway.py)")
        data = self.ag.gather_clean_data()
        self.log.info("Module (controller.py) using (database_gateway.py)")
        self.dg.connect_to_db()
        self.dg.create_tables()
        self.dg.add_auction_data(data)
        self.dg.close_connection()


if __name__ == '__main__':
    config_filepath = os.path.join(os.path.dirname(__file__), "data", "config")
    config_file = os.path.join(config_filepath, "my_config.json")
    con = Controller(config_file)
    con.collect_and_store_data()