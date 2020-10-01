import socket
from typing import Optional

import socks

_socket = socket.socket

SOCKS4 = socks.SOCKS4
SOCKS5 = socks.SOCKS5
HTTP = socks.HTTP

def start(
    proxy_type: int = SOCKS5,
    addr: str = "127.0.0.1",
    port: int = 9050,
    rdns: bool = True,
    username: Optional[str] = None,
    password: Optional[str] = None
    
) -> None:
    """Configura un proxy en un socket
    
    Args:
        proxy_type:
          Un entero que indica el tipo de proxy a usar

        addr:
          La dirección del proxy

        port:
          El puerto del proxy

        rdns:
          Transmitir al proxy que resuelva los nombres de dominio

        username:
          El nombre de usuario

        password:
          La contraseña
    """

    socks.set_default_proxy(proxy_type, addr, port,
                            rdns, username, password)
    socket.socket = socks.socksocket

def stop() -> None:
    """Restaura el socket original"""

    socket.socket = _socket
