import asyncio
import inspect
from typing import Dict, Any, Callable

from utils.extra import execute_possible_coroutine
from utils.extra import create_translation

_ = create_translation.create("parse_args")

POSITIONAL_ONLY = inspect._POSITIONAL_ONLY
POSITIONAL_OR_KEYWORD = inspect._POSITIONAL_OR_KEYWORD
VAR_POSITIONAL = inspect._VAR_POSITIONAL
KEYWORD_ONLY = inspect._KEYWORD_ONLY
VAR_KEYWORD = inspect._VAR_KEYWORD
empty = inspect._empty

class ConvertionException(Exception):
    def __init__(self, key, exception, *args, **kwargs):
        """
        Cuando la conversión entre tipos es inválida,
        pero es conveniente saberla explícitamente para
        dar el aviso al usuario-cliente o por la depuración.
        """

        super().__init__(*args, **kwargs)

        self.exception = exception
        self.key = key

class InvalidDataType(Exception):
    def __init__(self, key):
        """ Cuando el tipo de dato es inválido. """
        self.key = key

class RequiredArgument(Exception):
    def __init__(self, key, *args, **kwargs):
        """ Cuando un argumento es requerido y no está ajustado """

        super().__init__(*args, **kwargs)

        self.key = key

def parse(function: Callable[..., Any]) -> Dict[int, dict]:
    """Analiza una función y extrae los parámetros junto con
    sus argumentos pre-determinados (si los contiene)"""

    sig = inspect.signature(function)

    args = {
        POSITIONAL_ONLY       : {},
        POSITIONAL_OR_KEYWORD : {},
        VAR_POSITIONAL        : {},
        KEYWORD_ONLY          : {},
        VAR_KEYWORD           : {}

    }

    for name, parameter in sig.parameters.items():
        args[parameter.kind][name] = {
            "default"    : parameter.default,
            "annotation" : parameter.annotation

        }

    return args

def convert(key: str, value: Any, type: Callable[..., Any]) -> Any:
    """Trata de convertir un valor en otro tipo de datos"""

    if not (inspect.isclass(type)):
        raise InvalidDataType(key, _("El tipo de dato no es válido para continuar con la operación"))

    if (value is None) or \
       (type is empty) or \
       (isinstance(value, type)):
        return value

    try:
        return type(value)

    except Exception as err:
        raise ConvertionException(key, err, _("Error en la conversión de tipos"))

async def async_execute_function(function: Callable[..., Any], arguments: Dict[str, Any] = {}) -> Any:
    """Imita al usuario cuando llama a una función

    Esta función trata de imitar el comportamiento entre una
    función (o un objeto invocable) y un usuario que ingresa
    parámetros y argumentos.
    
    Args:
        function:
          La función a llamar

        arguments:
          Los parámetros y argumentos de la función a llamar

    Returns:
        Lo mismo que la función a llamar

    Raises:
        RequiredArgument: Falta un parámetro que es requerido
    """

    parse_args = parse(function)

    if (len(parse_args[VAR_POSITIONAL]) >= 1):
        args = list(arguments.values())
        kwargs = {}

    elif (len(parse_args[VAR_KEYWORD]) >= 1):
        args = []
        kwargs = arguments

    else:
        args = []
        kwargs = {}

    for key, value in parse_args[POSITIONAL_ONLY].items():
        if (value in args):
            continue

        default_value = value.get("default")
        annotation = value.get("annotation")
        
        try:
            real_value = arguments[key]

        except KeyError:
            if (default_value == empty):
                raise RequiredArgument(key, _("'{}' es necesario para poder continuar").format(key))

            else:
                real_value = default_value
        
        if (real_value is None):
            real_value = default_value

        args.append(
            convert(key, real_value, annotation)

        )

    for dictionary in (parse_args[POSITIONAL_OR_KEYWORD], parse_args[KEYWORD_ONLY]):
        for key, value in dictionary.items():
            if (key in kwargs):
                continue

            default_value = value.get("default")
            annotation = value.get("annotation")

            try:
                real_value = arguments[key]

            except KeyError:
                real_value = default_value
            
            if (real_value == empty):
                raise RequiredArgument(key, _("'{}' es necesario para poder continuar").format(key))
            
            if (real_value is None):
                real_value = default_value

            kwargs[key] = convert(key, real_value, annotation)

    return await execute_possible_coroutine.execute(
        function, *args, **kwargs

    )

def execute_function(*args, **kwargs):
    return asyncio.run(async_execute_function(*args, **kwargs))
