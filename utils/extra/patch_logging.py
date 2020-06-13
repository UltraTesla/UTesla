import logging
import gettext

from utils.General import replace_colors

from utils.extra import create_translation

language = 'es'
localedir = 'locales'

_logging_critical = logging.critical
_logging_error = logging.error
_logging_warning = logging.warning
_logging_info = logging.info
_logging_debug = logging.debug

def _func(msg, func, *args, **kwargs):
    _ = gettext.getcontroller
    msg = replace_colors.replace(msg)

    func(_(msg), *args, **kwargs)

def critical(msg, *args, **kwargs):
    _func(msg, _logging_critical, *args, **kwargs)

def error(msg, *args, **kwargs):
    _func(msg, _logging_error, *args, **kwargs)

def warning(msg, *args, **kwargs):
    _func(msg, _logging_warning, *args, **kwargs)

def info(msg, *args, **kwargs):
    _func(msg, _logging_info, *args, **kwargs)

def debug(msg, *args, **kwargs):
    _func(msg, _logging_debug, *args, **kwargs)

def apply():
    gettext.getcontroller = create_translation.create(
        'UTesla',
        localedir,
        language

    )

    gettext.gettext = create_translation.create(
        'argparse',
        localedir,
        language

    )

    logging.critical = critical
    logging.error = error
    logging.warning = warning
    logging.info = info
    logging.debug = debug
