import logging
import os
import inspect
import importlib
import pathlib
import glob

from utils.General import (exceptions,
                           remove_badchars,
                           listdir)
from utils.extra import logging_double
from config import defaults
from typing import NoReturn

complement_file: str = 'complements/'

def return_handle(filename: str) -> object:
    #complement = importlib.reload(
    #    importlib.import_module(filename)

    #)

    complement = importlib.import_module(filename)

    if not (hasattr(complement, 'Handler')):
        raise AttributeError('\'Handler\' no existe en el complemento: %s' % (filename))

    if not (inspect.isclass(complement.Handler)):
        raise exceptions.InvalidHandler('\'Handler\' no es una clase en: %s' % (filename))

    return complement.Handler

def list_only(path: str, recursive: bool = True) -> list:
    if (recursive):
        files =  pathlib.Path(path).rglob('*.py')

    else:
        files = glob.glob('%s/*.py' % (path))

    return files

def extract_modules(complement_name: str) -> dict:
    modules_object = {}

    complement_modules = '%s-%s' % (
        complement_name, defaults.modules_extension

    )

    modules = list_only(complement_modules)

    for module in modules:
        (module_path, _) = os.path.splitext(str(module))
        module_path = module_path.replace('/', '.')
        module_name = '.'.join(module_path.split('.')[2:]).replace(
            '-%s' % (defaults.modules_extension), ''

        )

        modules_object[module_name] = importlib.reload(
            importlib.import_module(module_path)

        )

    return modules_object

def callback_sub_services(name, files) -> NoReturn:
    complements = {}

    for file in files:
        (complement_path, _) = os.path.splitext(file)

        if (name is None):
            complement_name = complement_path.split('/', 1)[1].replace(
                '-%s' % (defaults.sub_services_extension), ''

            )

        else:
            complement_name = '%s/%s' % (
                name, complement_path.split('/', 2)[2]

            )

        complement2import = complement_path.replace('/', '.')

        try:
            complement_object = return_handle(complement2import)

        except AttributeError:
            continue

        if not (complement_name in complements):
            complements[complement_name] = {}

        complements[complement_name]['modules'] = extract_modules(complement_path)
        complements[complement_name]['handler'] = complement_object
        complements[complement_name]['mtime'] = os.path.getmtime(file)

        for _, vals in complements.items():
            for _, module in vals['modules'].items():
                setattr(module, 'modules', vals['modules'])

    return complements

def callback_main(dirname: str,
                  is_dir: bool,
                  exception: object,
                  complements: list) -> NoReturn:
    if (exception is not None):
        logging_double.log('Ocurrió un error listando algún directorio '
                           'o operando con un archivo')

        return

    if (dirname.endswith('-%s' % (defaults.sub_services_extension))):
        (name, _) = os.path.basename(dirname).split('-', 1)
        special_directory = (
            name, list_only(dirname)

        )

        complements.append(
            callback_sub_services(*special_directory)

        )

def show(sub_service: bool = True) -> dict:
    global complement_file
    
    complements = {}
    tracked_complements = []
    complement_file = os.path.basename(
        remove_badchars.remove(complement_file, '/')

    )

    if (sub_service):
        listdir.list(
            callback_main,
            complement_file,
            only_dirs=True,
            complements=tracked_complements

        )

        for complement in tracked_complements:
            complements.update(complement)

    complements.update(callback_sub_services(
        None, list_only(complement_file, sub_service)

    ))

    return complements
