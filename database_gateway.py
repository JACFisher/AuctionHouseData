#############################################
#
#
#
#############################################

import sqlite3
from generic_util import get_year_day, get_year_week, get_timestamp, initialize_logger
import os

_db_name = "ah_database.db"
_log_filename: str = "db_gateway.log"
_tables: dict = {
        "sales_table": {
            "name": "daily_listings",
            "columns": ["[item_id] INTEGER PRIMARY KEY", "[year] INTEGER NOT NULL", "[day_in_year] INTEGER NOT NULL"]
        },
        "table_names": {
            "name": "item_names",
            "columns": ["[ite8m_id] INTEGER FOREIGN KEY", "[item_name] TEXT DEFAULT 'UNDEFINED'"]
        }
}
for x in range(0,24):
    _tables["sales_table"]["columns"].append("[sales_at_hour_{}] INTEGER DEFAULT -1".format(x))


class DatabaseGateway(object):

    def __init__(self):
        self.today = get_year_day()
        self.log = initialize_logger("db_gateway")
        self.conn = None  # database connection
        self.cursor = None  # sqlite cursor

    def add_auction_data(self, cur_date, cur_time, data: dict):
        if self.conn is None or self.cursor is None:
            self.log.WARNING("Attempted to add data without a connection at: " + get_timestamp(human_readable=True))
        else:
            for keys in data.keys():
                pass

    def connect_to_db(self):
        try:
            self.log.info('###################### DATABASE ACCESS START ######################')
            path = os.path.join(os.path.dirname(__file__), 'database')
            db = os.path.join(path, _db_name)
            db = os.path.normpath(db)
            self.conn = sqlite3.connect(db)
            self.cursor = self.conn.cursor()
        except Exception as e:
            self.log.ERROR("FAILED TO CONNECT TO DATABASE")
            self.log.ERROR(e)

    def close_connection(self):
        self.log.info('####################### DATABASE ACCESS END #######################')
        self.conn.close()

    def create_tables(self):
        if self.conn is None or self.cursor is None:
            self.log.WARNING("Attempted to create tables without a connection at: " +
                             get_timestamp(human_readable=True))
        else:
            create = "CREATE TABLE IF NOT EXISTS"
            weekly_table = "weekly_listings_" + get_year_week()
            daily_table = "daily_listings_" + get_year_day()
            table_names = ['item_names', ]


if __name__ == '__main__':
    dg = DatabaseGateway()
    dg.connect_to_db()
    dg.close_connection()
