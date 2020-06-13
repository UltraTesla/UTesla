import logging

def log(msg, *args):
    logging.warning(msg, *args)
    logging.debug(msg, *args, exc_info=True)
