#######################################################################################################################
#
#   Manages database interactions and logs actions as appropriate  Connects/closes connection to the database,
#   creates any missing tables, fills data as given.  Returns results of queries.
#
#   Uses SQLite to avoid server connections for portability reasons.
#
#   For add_auction_data, data is expected in json (dict) format:
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
#   Alternatively, a single item_id and price can be provided separately with check_listing_table.
#
#######################################################################################################################

import sqlite3
import generic_util as gu
import os
# remove after testing:
import json

# global variables:
_db_path: str = os.path.join(os.path.dirname(__file__), "data", "database")
_db_name: str = "ah_database.db"
_log_filename: str = "db_gateway"
_listings: str = "weekly_listings_{}".format(gu.get_week())
_item_names: str = "item_names"
_sales_hour: str = "price_at_hour_"
_tables: dict = \
    {
        _listings: {
            "name": _listings,
            "columns": ["item_id INTEGER PRIMARY KEY", "year INTEGER NOT NULL", "day_in_year INTEGER NOT NULL"],
            "constraints": []
        },
        _item_names: {
            "name": _item_names,
            "columns": ["item_id INTEGER", "item_name TEXT DEFAULT 'UNDEFINED'"],
            "constraints": ["CONSTRAINT item_id FOREIGN KEY (item_id) REFERENCES listings (item_id)"]
        }
}
for x in range(0,24):
    _tables[_listings]["columns"].append("{}{} INTEGER DEFAULT -1".format(_sales_hour, x))


class DatabaseGateway(object):

    def __init__(self):
        self.today = gu.get_year_day()
        self.log = gu.initialize_logger("database_gateway.py")
        self.conn = None  # database connection
        self.cursor = None  # sqlite cursor

    def add_auction_data(self, sales_data: dict):
        if self.check_connection("add data to " + _item_names):
            for item_id in sales_data.keys():
                self.check_item_table(item_id)
        if self.check_connection("add data to " + _listings):
            for item_id in sales_data.keys():
                sales_this_hour = sales_data[item_id]["buyout"]
                if sales_this_hour == "NONE":
                    sales_this_hour = sales_data[item_id]["unit_price"]
                self.check_listing_table(item_id, sales_this_hour)

    def connect_to_db(self):
        try:
            time = "TIME: " + gu.get_timestamp()
            if not os.path.exists(_db_path):
                os.makedirs(_db_path)
            db = os.path.join(_db_path, _db_name)
            db = os.path.normpath(db)
            self.conn = sqlite3.connect(db)
            self.cursor = self.conn.cursor()
            self.log.info("###################### DATABASE ACCESS START ######################")
            self.log.info(time)
        except Exception as e:
            self.log.error("FAILED TO CONNECT TO DATABASE: " + db)
            self.log.error(time)
            self.log.error("Exception: " + str(e))

    def close_connection(self):
        if self.check_connection("close connection to " + _listings):
            self.log.info("TIME: {}".format(gu.get_timestamp()))
            self.log.info("####################### DATABASE ACCESS END #######################")
            self.conn.close()

    def create_tables(self):
        if self.check_connection("create tables"):
            self.log.info("Creating tables if they don't exist:")
            create = "CREATE TABLE IF NOT EXISTS {}"
            for table_data in _tables.keys():
                statement = create.format(_tables[table_data]["name"])
                count = 0
                for column in _tables[table_data]["columns"]:
                    if count == 0:  # need the first column to have an open parenthesis
                        statement += " ("
                        count += 1
                    else:  # the rest of the columns are comma-separated
                        statement += ", "
                    statement += column
                for constraint in _tables[table_data]["constraints"]:
                    statement += ", " + constraint
                statement += ")"  # statement ends with closed parenthesis either after columns or constraints
                self.execute_statement(statement, log_statement=True)

    def check_connection(self, message: str) -> bool:
        if self.conn is None or self.cursor is None:
            self.log.warning("Attempted to {} without a connection at {}.".format(
                            message, gu.get_timestamp(human_readable=True)))
            return False
        return True

    def execute_statement(self, statement: str, log_statement=False) -> bool:
        try:
            if log_statement:
                self.log.info("Executing statement: ")
                self.log.info(statement)
            self.cursor.execute(statement)
            self.conn.commit()
            return True
        except Exception as e:
            if not log_statement:
                self.log.info("Executing statement: ")  # If we didn't already log the statement,
                self.log.info(statement)                # do it now.
            self.log.error("Statement failed due to: ")
            self.log.error(e)
            return False

    def check_item_table(self, item_id: int):
        if self.check_connection("access " + _item_names):
            statement = "SELECT * FROM {} WHERE item_id={}".format(
                _tables[_item_names]["name"], str(item_id))
            if self.execute_statement(statement):
                if len(self.cursor.fetchall()) < 1:
                    statement = "INSERT INTO {} (item_id) VALUES ({})".format(
                        _tables[_item_names]["name"], str(item_id))
                    self.execute_statement(statement, log_statement=True)

    def check_listing_table(self, item_id: int, sales: int):
        if self.check_connection("access " + _listings):
            year = gu.get_year()
            day = gu.get_day()
            hour = gu.get_hour()
            statement = "SELECT * FROM {} WHERE item_id={} AND year={} AND day_in_year={}".format(
                _tables[_listings]["name"], str(item_id), year, day)
            if self.execute_statement(statement):
                if len(self.cursor.fetchall()) < 1:
                    statement = "INSERT INTO {} (item_id, year, day_in_year, {}{}) VALUES ({}, {}, {}, {})".format(
                        _tables[_listings]["name"], _sales_hour, hour,
                        str(item_id), year, day, str(sales))
                    self.execute_statement(statement)
                else:
                    statement = "UPDATE {} SET {}{} = {} WHERE item_id={} AND year={} AND day_in_year={}".format(
                        _tables[_listings]["name"], _sales_hour, hour, str(sales),
                        str(item_id), year, day)
                    self.execute_statement(statement)


#######################################################################################################################
#
#   The following exists for demonstration purposes only.
#   The true main entry point for this program is located in __main__.py
#
#######################################################################################################################


def load_sample_file():
    # There should be sample data in the auction_sample_data directory
    # There is a file on the repository, and the sample main in api_gateway writes data there as well
    # If for some reason there's nothing there, we do create a small fake dataset
    # FWIW, I have been using DB Browser (SQLite) to view data during testing,
    # and I have found it more than adequate if you wanted a suggestion!
    sample_data_folder = os.path.join(os.path.dirname(__file__), "data", "auction_sample_data")
    files = []
    if os.path.exists(sample_data_folder):
        files = os.listdir(sample_data_folder)
    if len(files) > 0 and ".json" in files[0]:
        filename = os.path.join(sample_data_folder, files[0])
        filename = os.path.normpath(filename)
        with open(filename, 'r') as rf:
            sales_data = json.load(rf)
            rf.close()
    else:  # if there is no sample data, create some fake data :)
        sales_data = {
            "32": {
                "buyout": 1337,
                "unit_price": "NONE"
            },
            "35": {
                "buyout": "NONE",
                "unit_price": 10534
            }
        }
    return sales_data


if __name__ == '__main__':
    dg = DatabaseGateway()
    dg.connect_to_db()
    dg.create_tables()
    data = load_sample_file()
    dg.add_auction_data(data)
    dg.close_connection()