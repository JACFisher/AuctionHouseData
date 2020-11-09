import datetime
import logging
import os.path
import sys

_log_folder: str = "logs"


def get_week() -> str:
    cur_week = datetime.datetime.now().timetuple().strftime("%U")
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


def initialize_logger(log_type="undefined"):
    day = get_year_day()
    today_log = day + "_" + log_type + ".log"
    filepath = os.path.join(os.path.dirname(__file__), _log_folder, log_type)
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    filename = os.path.join(filepath, today_log)
    logging.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG)
    logging.info('**************************************************')
    time = get_timestamp(human_readable=True)
    logging.info("Process started at: " + time)
    return logging

