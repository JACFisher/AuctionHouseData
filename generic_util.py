#######################################################################################################################
#
#   Utility functions used by other modules in this package.  Predominantly datetime methods and logging.
#
#######################################################################################################################

import datetime
import logging
import os.path

_log_folder: str = "logs"


def get_week() -> str:
    cur_week = datetime.datetime.now().strftime("%U")
    return str(cur_week)


def get_day() -> str:
    cur_day = datetime.datetime.now().timetuple().tm_yday
    return str(cur_day)


def get_year() -> str:
    cur_year = datetime.datetime.now().timetuple().tm_year
    return str(cur_year)


def get_year_week() -> str:
    year_plus_week = get_year() + "_" + get_week()
    return year_plus_week


def get_year_day() -> str:
    year_plus_day = get_year() + "_" + get_day()
    return year_plus_day


def get_timestamp(human_readable=True) -> str:
    cur_time = datetime.datetime.now().timestamp()
    if human_readable:
        human_readable = datetime.datetime.fromtimestamp(cur_time).isoformat()
        return human_readable
    else:
        return str(cur_time)


def get_hour() -> str:
    cur_hour = datetime.datetime.now().hour
    return str(cur_hour)


def initialize_logger(log_type="undefined") -> logging:
    day = get_year_day()
    today_log = day + "_" + log_type + ".log"
    filepath = os.path.join(os.path.dirname(__file__), _log_folder, log_type)
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    filename = os.path.join(filepath, today_log)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    new_handler = logging.FileHandler(filename, mode='a', encoding='utf-8')
    logger.addHandler(new_handler)
    logger.info('**************************************************')
    time = get_timestamp(human_readable=True)
    logger.info("Process started at: " + time)
    return logger
