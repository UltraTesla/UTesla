import re
import hashlib
import logging
import tornado.web
import urllib.parse

from modules.Infrastructure import dbConnector
from modules.Infrastructure import login
from modules.Infrastructure import exceptions
from modules.Infrastructure import client

from utils.General import show_complements
from utils.extra import execute_possible_coroutine
from utils.extra import logging_double

from config import defaults

# Los siguientes atributos de 'core_init' se deben definir
# en la importación y antes de instanciar 'CoreHandler'.

# El nombre de usuario del servidor, identificado por los
# demás servidores de la red
user_server: str = None

# La ruta de la carpeta de los usuarios
init_path: str = None

# El objeto para parsear el cuerpo de una petición
parse_object: object = None

# El objeto MySQL
pool_object: object = None

# Las direcciones permitidas para los servicios
host_list: str = '.*'

# El valor que será usado en el encabezado 'Access-Control-Allow-Origin'
access_control_allow_origin = '*'

class CoreHandler(tornado.web.RequestHandler):
    def _generate_complement_list(self):
        complements = []

        for name, value in show_complements.show().items():
            handler = value['handler']
            handler.write = self.write
            handler.set_defaults_headers = self.set_default_headers
            handler.prepare = self.prepare
            handler.head = self.head

            def __init__(self):
                self.modules = value['modules']

            handler.__init__ = __init__

            complements.append(
                ('/' + name + '(/*)$', handler())

            )

        return complements

    def _check_url(self):
        path = self.request.path

        logging.debug('Verificando la existencia de la ruta...')

        if (path == '/'):
            logging.debug('Es el directorio raíz, no se hace nada...')

            return (True, None)

        for (url, handler) in self._generate_complement_list():
            if (re.match(url, path)):
                logging.debug('Se ha accedido a MATCH("%s", "%s")', url, path)

                return (True, handler)

        return (False, None)

    def set_default_headers(self):
        self.set_header('Server', 'UltraTesla/1.0')
        self.set_header('Content-Type', defaults.default_type)
        self.set_header('Access-Control-Allow-Origin',
                        access_control_allow_origin)

    async def write(self, chunk):
        logging.debug('Enviando datos al usuario "%s" (%s) - %s %s' % (
            self.user,
            self.request.remote_ip,
            self.request.method,
            self.request.path

        ))
        
        data = await parse_object.reply(self.user, chunk)

        super().write(
            data

        )

    async def prepare(self):
        exception = True
        status_code = 500

        try:
            await self.post_prepare()

        except (exceptions.InvalidRequest, exceptions.PublicKeyNotFound) as err:
            status_code = 401

            logging_double.log('Ocurrió un posible error referente a la petición o a un contexto relacionado a ella: %s', err)

        except (exceptions.TokenLimitsExceeded) as err:
            status_code = 202

            logging_double.log('Error de procesamiento: %s', err)

        except Exception as err:
            status_code = 500

            logging_double.log('Ocurrió un posible error de ejecución: %s', err)

        else:
            exception = False

        if (exception):
            self.set_status(status_code)
            self.finish()

    async def render(self, *args, **kwargs):
        await self.write(
            self.render_string(*args, **kwargs)

        )

    def write_error(self, status_code, **kwargs):
        pass

    def get_argument(self, name, default=None):
        if (self.request.method in defaults.write_methods):
            return self.body.get(name, default)

        else:
            return self.get_query_argument(name, default)

    def get_arguments(self, name):
        value = self.get_argument(name, None)

        if (isinstance(value, list)):
            return value

    # Parsear el cuerpo de la petición sería diferente, ya
    # que usa ProtoTesta, pero para las peticiones GET, no
    # cambiaría nada.
    get_body_argument = get_argument
    get_body_arguments = get_arguments

    async def remote_interact(self):
        status_code = 404

        if (self.force_url):
            url_split = urllib.parse.urlsplit(self.request.path[1:])

            if not (url_split.netloc):
                logging.warning('¡La dirección está vacía!')

                return 400

            if not (url_split.scheme in ['http', 'https']):
                logging.warning('¡El esquema de "%s" no es correcto!',
                                url_split.get_url())
                
                url_split = url_split._replace(scheme='http')

            sub_split = urllib.parse.urlsplit(url_split.path[1:])

            if not (sub_split.path) or (sub_split.path == '/'):
                logging.warning('¡El servicio o sub-servicio de "%s" no es correcto o no está permitido!',
                                url_split.get_url())

                return 400

            service_url = '%s://%s' % (
                url_split.scheme, url_split.netloc

            )

        else:
            service_name = self.request.path[1:].split('/')[0]

        aux_networkid = None

        Client = client.UTeslaClient(
            user_server, parse_object.rsa

        )
        Client.set_headers(self.request.headers)

        # Para no repetir tanto código con puros if elif else...
        async def local_service2url():
            yield service_url

        # Si se ajusta "force_url", el usuario podrá
        # elegir arbitrariamente el nodo en la red, 
        # si es que éste existe.
        if (self.force_url):
            aux_networkid = await self.db.extract_networkid(service_url)

            if (aux_networkid is None):
                logging.warning('¡La dirección "%s" no forma parte de la red!', url)

                return 404

            urls = local_service2url()

        else:
            urls = self.db.service2url(service_name, True)
        
        async for url in urls:
            # Para no volver a perder tiempo y rendimiento, se usa un auxiliar
            # y usar el mismo identificador de red que se extrajo anteriormente
            # cuando es un petición arbitraria.
            if (aux_networkid is not None):
                # Sinónimo para evitar conflictos
                node = '%s/%s' % (
                    url, url_split.path[1:]

                )
                network = url
                networkid = aux_networkid
                # Por si acaso no es una petición arbitraria y evitar malos tragos
                aux_networkid = None

            else:
                (networkid, network) = url

                node = '%s/%s' % (
                    network, self.request.path[1:]

                )

            token = await self.db.get_network_token(networkid)

            cmd = {
                'token' : token,
                'body'  : self.body

            }

            url_hash = hashlib.sha3_224(
                network.encode()

            ).hexdigest()
            public_key = '%s/servkeys/%s' % (
                init_path, url_hash

            )

            await Client.set_server_key(public_key)
            
            try:
                response = await Client.fetch(
                    node, cmd, self.request.method, raise_error=False

                )

            except Exception as err:
                status_code = 202

                logging_double.log('Ocurrió un error al conectar a "%s": %s', node, err)
                continue

            else:
                for key, value in response.headers.items():
                    self.set_header(key, value)

                response_dec = Client.get_message(response.body)

                await self.write(response_dec)

                status_code = response.code

        return status_code

    async def post_prepare(self):
        method = self.request.method.lower()
        self.db = dbConnector.UTeslaConnector(pool_object)

        (user_hash, parse_args) = await parse_object.destroy(
            self.request.body

        )

        self.user = await self.db.hash2user(user_hash)

        (self.path_exists, self.handler) = self._check_url()

        self.message = {
            'error'   : False,
            'message' : None

        }

        self.cmd = parse_args.get('cmd')
        self.token = parse_args.get('token')
        self.args = parse_args.get('args', {})
        self.body = parse_args.get('body', {})
        self.force_url = bool(parse_args.get('force_url', False))

        if not (self.request.headers.get('Content-Type') in defaults.content_types):
            self.set_status(412)

            return

        if not (re.match(host_list, self.request.headers.get('Host'))):
            # A pesar de que puedas existir, si no está en la lista blanca
            # se le considera un posible peligro, por lo que se le miente.
            self.set_status(404)

            logging.warning('%s no está en la lista blanca del encabezado \'Host\'',
                            self.request.headers.get('Host'))

            return

        if not (self.cmd in defaults.no_token_required):
            if (self.token is None):
                self.set_status(401)

                self.message['error'] = True
                self.message['message'] = 'Es necesario el token para realizar esta operación'

            else:
                token_exists = await self.db.token_exists(self.token)

                if (token_exists):
                    is_expired = await self.db.is_expired(self.token)

                    if (is_expired):
                        self.set_status(401)

                        self.message['error'] = True
                        self.message['message'] = 'El token ha expirado'

                        await self.db.delete_token(self.token)

                        logging.debug('El token "%s" se ha eliminado por su fecha de expiración' % (
                            self.token

                        ))

                else:
                    self.set_status(401)

                    self.message['error'] = True
                    self.message['message'] = 'Permiso denegado'

        if (self.cmd is not None) and not (self.message['error']):
            userid = await self.db.extract_userid(self.user)
            login_cmd = login.Login(
                self.user, userid,
                init_path, self.db,
                parse_object.rsa

            )
            
            if not (userid):
                self.set_status(401)

                self.message['error'] = True
                self.message['message'] = 'El nombre de usuario no existe'

            elif (hasattr(login_cmd, self.cmd)):
                (status, response) = await execute_possible_coroutine.execute(
                    getattr(login_cmd, self.cmd), **self.args

                )

                self.set_status(status)

                self.message['message'] = {
                    'status'   : status,
                    'response' : response

                }

            else:
                self.set_status(404)
                
                self.message['error'] = True
                self.message['message'] = 'Comando no existente'

        if (self.message['message']):
            await self.write(self.message)

            return

        if (self.path_exists):
            if (hasattr(self.handler, method)):
                await execute_possible_coroutine.execute(
                    getattr(self.handler, method)

                )

            else:
                self.set_status(405)

        else:
            remote_status = await self.remote_interact()

            self.set_status(remote_status)

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass

    def put(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def head(self, *args, **kwargs):
        pass

    def options(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Methods',
                        ', '.join(self.SUPPORTED_METHODS))

    def patch(self, *args, **kwargs):
        pass
