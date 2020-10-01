import os
import logging
import configparser
import gettext

from config import defaults

cache = {}

logging.basicConfig(format="%(levelname)s: %(message)s")

def parse(use_cache: bool = True) -> dict:
    """Parsear la configuración
    
    Args:
        use_cache:
          De forma global se almacena un diccionario que contiene toda la configuración,
          si ``use_cache`` es **True** se retorna ese diccionario en vez de parsear el
          archivo de configuración por cada invocación, lo cual mejoraría el rendimiento.

    Returns:
        Un diccionario con la configuración parseada.
    """

    global cache

    if (use_cache) and (cache):
        return cache

    config = configparser.ConfigParser(
        defaults.defaults,
        empty_lines_in_values = False,
        interpolation = None

    )
    config.read(defaults.fileconfig)

    for section, values in defaults.dictionary.items():
        for (value, type) in values:
            default = defaults.defaults[section][value]
            env_default = os.getenv("UTESLA_{}_{}".format(section, value))

            if (type == bool):
                convert = config.getboolean

            elif (type == int):
                convert = config.getint

            elif (type == float):
                convert = config.getfloat

            else:
                convert = config.get

            if not (section in cache):
                cache[section] = {}

            try:
                aux = convert(
                    section, value, fallback=env_default or default

                )

            except Exception as err:
                logging.exception(
                    "Exception captada al analizar la sección '%s' y el valor de clave '%s' %s",
                    section, value
                        
                )

                aux = default

                logging.warning(
                    "Usando el valor '%s' en la clave '%s' sobre la sección '%s'",
                    aux, value, section
                    
                )

            finally:
                cache[section][value] = aux

            if (aux in defaults.default_dictionary):
                cache[section][value] = defaults.default_dictionary[aux]

    return cache
