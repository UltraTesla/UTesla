import logging
import logging.config
import json

from utils.General import replace_colors

def init(logging_conf):
    with open(logging_conf.get("log_config"), "r") as log_config_fd:
        logging.config.dictConfig(
            json.load(log_config_fd)

        )

    for levelName in ("critical",
                      "error",
                      "warning",
                      "info",
                      "debug"):
        logging_conf[levelName] = replace_colors.replace(
            logging_conf.get(levelName)

        )

    logging.addLevelName(logging.CRITICAL, logging_conf.get("critical")) # CRITICAL - 50
    logging.addLevelName(logging.ERROR, logging_conf.get("error"))       # ERROR    - 40
    logging.addLevelName(logging.WARNING, logging_conf.get("warning"))   # WARNING  - 30
    logging.addLevelName(logging.INFO, logging_conf.get("info"))         # INFO     - 20
    logging.addLevelName(logging.DEBUG, logging_conf.get("debug"))       # DEBUG    - 10
