from inspect import namedtuple
from typing import Tuple

from utils.extra import create_translation

_ = create_translation.create("netparse")

def __set_correct_path(path):
    if (path != "/") and (path[:1] != "/"):
        path = "/" + path

    return path

def __check_port(port):
    try:
        port = int(port)

    except ValueError:
        raise ValueError(_("Puerto inválido"))

    else:
        if (port < 0) or (port > 65535):
            raise ValueError(_("Puerto inválido"))

    return port

def parse(net: str, default_port: int = 17000, default_path: str = "/") -> Tuple[str, int, str]:
    """Parsea una dirección
    
    Esta función convierte una cadena como `localhost:17000/service`
    en algo más manejable como `Network(address, port, path)`.

    Args:
        net:
          La dirección parsear

        default_port:
          Si `net` no se especifica un puerto, se usa el valor por
          defecto de esta opción.

        default_path:
          Si `path` no se especifica la ruta del servicio, se usa
          el valor por defecto de esta opción.

    Returns:
        Una tupla con la dirección, el puerto y la ruta del servicio

    Raises:
        ValueError: Cuando el puerto sea inválido
    """

    info = {}
    path = None
    port = None

    default_path = __set_correct_path(default_path)

    network = namedtuple(
        "Network",
        ("address", "port", "path"),
        defaults=(__check_port(default_port), default_path)

    )

    try:
        (addr, path) = net.split("/", 1)

    except ValueError:
        (addr,) = net.split("/", 1)

    else:
        if not (path):
            path = "/"

    try:
        (addr, port) = addr.split(":", 1)

    except ValueError:
        (addr,) = addr.split(":", 1)

    else:
        port = __check_port(port)

    info["address"] = addr

    if (path is not None):
        info["path"] = __set_correct_path(path)

    if (port is not None):
        info["port"] = port

    return network(**info)
