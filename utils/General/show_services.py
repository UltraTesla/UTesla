import os
import pathlib
import importlib
import inspect
import logging
from typing import (
    Iterator,
    Union,
    Tuple
    
)

import tornado.autoreload

from utils.extra import remove_badchars
from utils.extra import create_translation

from config import defaults

_ = create_translation.create("show_services")

class HandlerAux(object):
    pass

def return_handle(
    filename: str,
    ext: str,
    autoreload: bool = False
    
) -> object:
    """Importa un archivo de python

    Importar un archivo y a la misma vez lo analiza para obtener una
    clase para ser usada como un servicio.
    
    Args:
        filename:
          La ruta del archivo

        ext:
          La extensión del archivo

        autoreload:
          **True** para autorecargar el módulo al ser modificado.
          Tiene que estar habilitado con `tornado.autoreload.start()`

    Returns:
       La clase del servicio
    """

    service2import = filename.replace("/", ".")

    if (autoreload):
        tornado.autoreload.watch(filename + ext)

    service = importlib.import_module(service2import)

    if not (hasattr(service, defaults.handler_name)):
        logging.warning(_("'%s' no existe en el servicio: %s"), defaults.handler_name, filename)
        return HandlerAux

    handler = getattr(service, defaults.handler_name)

    if not (inspect.isclass(handler)):
        logging.warning(_("'%s' no es una clase en: %s"), defaults.handler_name, filename)
        return HandlerAux

    return handler

def parse_path(filename: str) -> str:
    """Convierte un nombre de archivo (sin extensión) en un
    nombre de servicio válido.

    Raises:
        ValueError: En caso de que el nombre sea inválido
    """

    filename = remove_badchars.remove(filename, "/")
    parsed = filename

    try:
        parsed = filename.split("/", 1)[1]

    except IndexError:
        raise ValueError(_("Nombre inválido"))

    if not (parsed):
        parsed = filename

    return parsed

def get_module(
    file: str,
    autoreload: bool = False, *,
    return_name: bool = False,
    only_name: bool = False
    
) -> Union[Tuple[str, object], object]:
    """Importa un archivo de python

    A diferencia de `return_handle()` esta función hace muchas más cosas,
    como: nombrar correctamente al archivo, importarlo, analizarlo, etc.

    Es recomendable usar esta función y no `return_handler`.
    
    Args:
        file:
          La ruta del archivo a importar

        autoreload:
          **True** para autorecargar el módulo al ser modificado.
          Tiene que estar habilitado con `tornado.autoreload.start()`

        return_name:
          Retornar el nombre de la clase y la clase misma si es **True**;
          **False** si no.

        only_name:
          **True** para mostrar solo el nombre.
          Esta opción no carga el archivo en memoria, simplemente busca
          y parsea el nombre.

    """

    file = remove_badchars.remove(file, "/")
    (service_path, extension) = os.path.splitext(file)

    service_name = parse_path(service_path)

    if not (only_name):
        service_object = return_handle(service_path, extension, autoreload)

        if (return_name):
            return (service_name, service_object)

        else:
            return service_object

    else:
        return service_name

def get_service(
    file: str,
    autoreload: bool = False,
    basename: bool = False,
    only_name: bool = False
    
) -> Tuple[str, object]:
    """Importa un archivo de python jutno con información relevante

    Args:
        file:
          La ruta del archivo a importar

        autoreload:
          **True** para autorecargar el módulo al ser modificado.
          Tiene que estar habilitado con `tornado.autoreload.start()`

        basename:
          Usar el nombre del servicio y no su ruta completa

        only_name:
          **True** para mostrar solo el nombre.
          Esta opción no carga el archivo en memoria, simplemente busca
          y parsea el nombre.
    
    Returns:
        Una tupla con la información extraida
    """

    result = get_module(file, return_name=True, only_name=only_name)

    if not (only_name):
        (service_name, service_object) = result

        if (basename):
            service_name = os.path.basename(service_name)

        return (service_name, service_object)

    else:
        if (basename):
            result = os.path.basename(result)

        return result

def show(
    service_file: str = "services/",
    sub_service: bool = True,
    autoreload: bool = False,
    only_name: bool = False

) -> Iterator[dict]:
    """Muestra la información extraida de cada 

    Args:
        service_file:
          La ubicación de la carpeta de los servicios

        sub_service:
          **True** para mostrar los sub-servicios; **False**
          de lo contrario.

        autoreload:
          **True** para autorecargar el módulo al ser modificado.
          Tiene que estar habilitado con `tornado.autoreload.start()`

        only_name:
          **True** para mostrar solo el nombre.
          Esta opción no carga el archivo en memoria, simplemente busca
          y parsea el nombre.

    Returns:
        Un iterador que contiene una con la información del
        servicio actualmente analizado.
    """

    service_file = remove_badchars.remove(service_file, "/")

    for dir in pathlib.Path(service_file).iterdir():
        if not (dir.is_dir()):
            continue

        index = "%s/%s.py" % (dir.as_posix(), dir.name)

        if not (os.path.isfile(index)):
            logging.warning(_("No existe '%s.py' en el servicio '%s'"), dir.name, dir.as_posix())

        else:
            yield get_service(index, autoreload, True, only_name)

        if (sub_service):
            for file in pathlib.Path(dir).rglob("*.py"):
                if (file.as_posix() != index) and (file.is_file()):
                    yield get_service(file.as_posix(), autoreload, only_name=only_name)
