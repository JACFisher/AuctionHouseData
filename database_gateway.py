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
            "name": "listings",
            "columns": ["item_id INTEGER PRIMARY KEY", "year INTEGER NOT NULL", "day_in_year INTEGER NOT NULL"],
            "constraints": []
        },
        "names_table": {
            "name": "item_names",
            "columns": ["item_id INTEGER", "item_name TEXT DEFAULT 'UNDEFINED'"],
            "constraints": ["CONSTRAINT item_id FOREIGN KEY (item_id) REFERENCES listings (item_id)"]
        }
}
for x in range(0,24):
    _tables["sales_table"]["columns"].append("sales_at_hour_{} INTEGER DEFAULT -1".format(x))


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
            for key in data.keys():
                self.check_item_table(key)

    def connect_to_db(self):
        try:
            time = "TIME: " + get_timestamp()
            filepath = os.path.join(os.path.dirname(__file__), "database")
            db = os.path.join(filepath, _db_name)
            db = os.path.normpath(db)
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            self.conn = sqlite3.connect(db)
            self.cursor = self.conn.cursor()
            self.log.info("###################### DATABASE ACCESS START ######################")
            self.log.info(time)
        except Exception as e:
            self.log.error("FAILED TO CONNECT TO DATABASE: " + db)
            self.log.error(time)
            self.log.error("Exception: " + str(e))

    def close_connection(self):
        time = "TIME: " + get_timestamp()
        if self.conn is None or self.cursor is None:
            self.log.warning("Attempted to close an unopen connection at: " +
                             time)
        else:
            self.log.info(time)
            self.log.info("####################### DATABASE ACCESS END #######################")
            self.conn.close()

    def create_tables(self):
        if self.conn is None or self.cursor is None:
            self.log.warning("Attempted to create tables without a connection at: " +
                             get_timestamp(human_readable=True))
        else:
            self.log.info("Creating tables if they don't exist.")
            create = "CREATE TABLE IF NOT EXISTS {}";
            for table_data in _tables.keys():
                statement = create.format(_tables[table_data]["name"])
                count = 0;
                for column in _tables[table_data]["columns"]:
                    if count == 0:  # need the first column to have an open parenthesis
                        statement += " ("
                        count += 1
                    else:  # the rest of the columns are comma-separated
                        statement += ", "
                    statement += column
                for constraint in _tables[table_data]["constraints"]:
                    statement += ", " + constraint
                statement += ")"
                self.execute_statement(statement)

    def execute_statement(self, statement) -> bool:
        try:
            self.log.info("Executing statement: ")
            self.log.info(statement)
            self.cursor.execute(statement)
            self.conn.commit()
            return True
        except Exception as e:
            self.log.error("Statement failed due to: ")
            self.log.error(e)
            return False

    def check_item_table(self, item_id: int):
        if self.conn is None or self.cursor is None:
            self.log.warning("Attempted to access item_names without a connection at: " +
                             get_timestamp(human_readable=True))
        else:
            statement = "SELECT * FROM {} WHERE item_id={}".format(
                _tables["names_table"]["name"], str(item_id))
            if self.execute_statement(statement):
                if len(self.cursor.fetchall()) < 1:
                    statement = "INSERT INTO {} (item_id) VALUES ({})".format(
                        _tables["names_table"]["name"], str(item_id))
                    self.execute_statement(statement)


if __name__ == '__main__':
    dg = DatabaseGateway()
    dg.connect_to_db()
    dg.create_tables()
    dg.check_item_table(35)
    dg.close_connection()
