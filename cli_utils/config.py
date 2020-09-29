import os
import sys
import copy
import inspect
import importlib

from cli_utils import exceptions
from utils.extra import create_translation

from config import defaults

_ = create_translation.create("cli_utils")

def _get_info(obj):
    if not (hasattr(obj, defaults.information_name)):
        raise exceptions.InformationNotFoundError(_("El diccionario '{}' no existe").format(
            defaults.information_name
            
        ))

    information = getattr(obj, defaults.information_name)

    if not (isinstance(information, dict)):
        raise TypeError(_("Tipo de dato incorrecto en el diccionario '{}'").format(
            defaults.information_name
            
        ))

    description = information.get("description") or ""
    workspaces = information.get("workspaces") or []
    commands = information.get("commands") or ()
    version = information.get("version")
    persist = information.get("persist") or False
    index = information.get("index") or 0

    if not (isinstance(description, str)):
        raise TypeError(_("El tipo de dato de la descripción es incorrecto"))

    if not (isinstance(workspaces, list)):
        raise TypeError(_("El tipo de dato de los espacios de trabajos es incorrecto"))

    if not (isinstance(commands, (list, tuple))):
        raise TypeError(_("El tipo de dato de las opciones para la línea de comandos es incorrecto"))

    if (version is not None) and not (isinstance(version, (int, float, str))):
        raise TypeError(_("El tipo de dato del número de versión es incorrecto"))

    if not (isinstance(persist, (int, bool))):
        raise TypeError(_("El tipo de dato de la opción de persistencia en incorrecto"))

    if not (isinstance(index, (str, int))):
        raise TypeError(_("El tipo de dato del índice que indica qué espacio de trabajos usar es incorrecto"))
    
    else:
        # Si es un string se convierte a un entero
        index = int(index)

    return {
        "description" : description,
        "workspaces"  : workspaces,
        "commands"    : commands,
        "version"     : version,
        "persist"     : persist,
        "index"       : index
            
    }

def _file2module_name(filename):
    return filename.replace("/", ".")

def load(filename):
    module = _file2module_name(filename)
    obj = importlib.import_module(module)

    return _get_info(obj)

def get_config(filename):
    return load(filename)

def get_function(work_options, options):
    filename = options.get("filename")
    target = options.get("workspaces")
    index = options.get("index")
    (no_add_path, no_restore, arg_index, path) = work_options

    if (no_restore):
        bak_path = copy.copy(sys.path)
    
    workspace_name = "%s-%s" % (filename, defaults.workspace_extension)

    if (no_add_path) and (os.path.isdir(workspace_name)):
        workspaces = [workspace_name]

    else:
        workspaces = []

    module = _file2module_name(filename)

    target.extend(workspaces)
    target.extend(path)

    last_index = len(target)-1

    if (arg_index < 0):
        options["index"] = 0

    elif (arg_index > last_index):
        options["index"] = last_index

    else:
        options["index"] = arg_index

    sys.path = target + sys.path

    obj = importlib.import_module(module)

    if (no_restore):
        sys.path = bak_path

    if not (hasattr(obj, defaults.mainparser_name)):
        raise exceptions.MainFunctionNotFoundError(
            _("La función '{}' no existe").format(defaults.mainparser_name)
            
        )

    function = getattr(obj, defaults.mainparser_name)

    if not (inspect.isfunction(function)) and (callable(function)):
        raise TypeError(_("'{}' no es una función").format(defaults.mainparser_name))

    inspection = inspect.getfullargspec(function)

    if (len(inspection.args) != 1):
        raise TypeError(
            _("La función '{}' debe recibir sólo un argumento").format(defaults.mainparser_name)
            
        )

    if (len(inspection.kwonlyargs) > 0):
        raise TypeError(
            _("La función '{}' no debe recibir argumentos clave").format(defaults.mainparser_name)

        )

    return function
