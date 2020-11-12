#######################################################################################################################
#
#   Main entry into the program.  Should use a task scheduler such as Windows Task Scheduler or
#   cron to run this every hour.
#
#######################################################################################################################

import os
from controller import Controller


def main():
    config_filepath = os.path.join(os.path.dirname(__file__), "data", "config")
    config_file = os.path.join(config_filepath, "my_config.json")
    controller = Controller(config_file)
    controller.main()


if __name__ == '__main__':
    main()
