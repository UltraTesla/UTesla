
import socket
import socks

_socket = socket.socket

SOCKS4 = socks.SOCKS4
SOCKS5 = socks.SOCKS5
HTTP = socks.HTTP

def start(proxy_type=SOCKS5, addr='127.0.0.1', port=9050,
          rdns=True, username=None, password=None):
    socks.set_default_proxy(proxy_type, addr, port,
                            rdns, username, password)
    socket.socket = socks.socksocket

def stop():
    socket.socket = _socket
