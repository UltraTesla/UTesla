import asyncio
import logging
import tornado.web
import tornado.httpserver
import tornado.ioloop

# El verdadero núcleo
from modules.Infrastructure import core_init

# Las configuraciones extras de tornado
options: dict = {}

class MainHandler(core_init.CoreHandler):
    pass

def make_app():
    return tornado.web.Application([
        (r'/(.*)', MainHandler)

    ], debug=True)

def start(lhost: str,
          lport: int):
    logging.info('Escuchando en %s:%d', lhost, lport)

    server = tornado.httpserver.HTTPServer(
        make_app(), **options

    )

    server.listen(lport, lhost)
