import re
import os
import time
import logging
import asyncio
import inspect

from typing import Optional, Callable, Any, AsyncIterator, Tuple, Union

import tornado.tcpserver
import aiofiles
import nacl

from modules.Infrastructure import errno
from modules.Infrastructure import exceptions
from modules.Infrastructure import options
from modules.Infrastructure import utils
from modules.Crypt import ed25519
from modules.Crypt import x25519_xsalsa20_poly1305MAC

from utils.General import show_services
from utils.General import (proc_control, proc_stream)
from utils.extra import remove_badchars
from utils.extra import procs_repr
from utils.extra import parse_args
from utils.extra import execute_possible_coroutine
from utils.extra import counter
from utils.extra import create_translation

from config import defaults

_ = create_translation.create("core")
logger = logging.getLogger(__name__)

class MainDataControl(utils.MainServer):
    def __init__(
        self,
        pool: object,
        user_length: int,
        public_key_length: int,
        headers_length: int,
        memory_limit: int,
        recv_timeout: int,
        *args, **kwargs

    ):
        super().__init__(user_length=user_length, *args, **kwargs)

        self.pool = pool
        self.user_length = user_length
        self.public_key_length = public_key_length
        self.headers_length = headers_length
        self.memory_limit = memory_limit
        self.recv_timeout = recv_timeout

    def __set_headers(self, data):
        # Si no es un diccionario, por lo tanto, escabezados inválidos
        if not (isinstance(data, dict)):
            return

        # Se evita que un servicio introduzca datos incorrectos que puedan
        # ocasionar alguna inestabilidad con otro servicio.
        self.request.headers = {}
        self.request.headers.update(data)

        # Lectura fácil
        self.request.path = data.get("path")
        self.request.action = data.get("action")
        self.request.token = data.get("token")
        self.request.params = data.get("params", {})
        self.request.init_params = data.get("init_params", {})
        self.request.force = data.get("force", False)
        self.request.node = data.get("node", ())
        self.request.is_packed = data.get("is_packed", True)
        
        # Ajustamos los encabezados del cliente
        self.request.set_header("path", self.request.path, str)
        self.request.set_header("action", self.request.action, str)
        self.request.set_header("token", self.request.token, str)
        self.request.set_header("force", self.request.force, bool)
        self.request.set_header("node", self.request.node, tuple)
        self.request.set_header("is_packed", self.request.is_packed, bool)
        self.request.set_header("params", self.request.params, dict)
        self.request.set_header("init_params", self.request.init_params, dict)
        self.request.set_header("status_code", data.get("status_code", 0), int)
        self.request.set_header("status", data.get("status", ""), str)

        # Y ahora ajustamos el mismo valor del cliente pero para el servidor
        self.set_header("path", self.request.path, str)
        self.set_header("action", self.request.action, str)

    async def initialize(self) -> AsyncIterator[Any]:
        real_user = await self.recv_data(
            self.user_length,
            timeout = self.recv_timeout
            
        )
        self.request.set_real_user(real_user)

        user = await self.pool.return_first_result("hash2user", real_user.hex())
        
        if (user is not None):
            (user,) = user

        else:
            logger.warning(_("El nombre de usuario real '%s' no existe"), real_user.hex())
            return

        self.request.set_user(user)

        userid = await self.pool.return_first_result("extract_userid", user)
        
        # ``userid```no debería hacer referencia a **None**, por lo
        # tanto es un error interno del servidor.
        if (userid is not None):
            (userid,) = userid

        else:
            logger.warning(_("Hubo un problema extrayendo el identificador del usuario '%s'"), user)
            return

        self.request.set_userid(userid)

        public_key = await self.recv_data(
            self.public_key_length,
            timeout = self.recv_timeout
            
        )
        verifyKey = os.path.join(
            self.init_path,
            self.user_data,
            real_user.hex()
                
        )

        if not (os.path.isfile(verifyKey)):
            raise exceptions.PublicKeyNotFound(
                _("Error, la clave '{}' no existe").format(verifyKey)

            )
        
        async with aiofiles.open(verifyKey, "rb") as fd:
            self.set_session(
                ed25519.verify((await fd.read()), public_key)
            
            )

        await self.shareKey()

        self.request.is_guest_user = await self.pool.return_first_result(
            "is_guest_user", userid

        )

        while (True):
            self.__set_headers(
                await self.read(
                    self.headers_length,
                    timeout = self.recv_timeout
                    
                )
                    
            )

            # Si la acción no es definida, se para la ejecución hasta este punto, ya que seguir
            # implica mucho procesamiento innecesario.
            if not (self.request.action):
                await self.write_status(errno.ECLIENT, _("No se indicó ninguna acción"))
                return

            if not (self.request.path):
                await self.write_status(errno.ECLIENT, _("No se indicó ningún servicio"))
                return

            fut = self.read(self.memory_limit,
                            timeout=self.recv_timeout,
                            is_packed=self.request.is_packed)

            yield await fut

class RequestController(utils.MainParameters):
    def __init__(
        self,
        template: object,
        headers: dict,
        request: "Request()",
        pool: object,
        write_function: Callable[[Any, Optional[dict]], None],
        write_status_function: Callable[[int, str, Any], None],
        procs: "Procedures()",
        body: AsyncIterator[Any],
        data: Optional[Any] = None
        
    ):
        self.__template = template
        self.__request = request
        self.__pool = pool
        self.__write_function = write_function
        self.__write_status_function = write_status_function
        self.__procs = procs
        self.__body = body
        self.data = data
        self.headers = headers

    @property
    def template(self):
        return self.__template

    @property
    def request(self):
        return self.__request

    @property
    def pool(self):
        return self.__pool

    @property
    def write(self):
        return self.__write_function

    @property
    def write_status(self):
        return self.__write_status_function

    @property
    def procs(self):
        return self.__procs

    @property
    def body(self):
        return self.__body

class CustomTemplate(utils.Templates):
    def __init__(self, template: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__template = template
        self.__exp_func = None

    def set_function_expression(self, function: Callable[..., Any]) -> None:
        if not (inspect.isfunction(function)):
            raise TypeError(_("No es una función"))
        
        self.__exp_func = function

    def get_template(self, *args, **kwargs) -> Optional[str]:
        if (self.__exp_func is None) or (self.__exp_func(*args, **kwargs)):
            return super().generate_template(self.__template)

class MainHandler(tornado.tcpserver.TCPServer):
    def __init__(
        self,
        pool_object: object,
        procs: "Procedures()",
        utesla_version: str,
        templates: dict,
        user_server: str = options.USER_SERVER,
        init_path: str = options.INIT_PATH,
        user_data: str = options.USER_DATA,
        memory_limit: int = options.MEMORY_LIMIT,
        headers_length: int = options.HEADERS_LENGTH,
        user_length: int = options.USER_LENGTH,
        public_key_length: int = options.PUBLIC_KEY_LENGTH,
        service_file: str = options.SERVICE_FILE,
        index_name: str = options.INDEX_NAME,
        admin_service: str = options.ADMIN_SERVICE,
        recv_timeout: int = options.RECV_TIMEOUT,
        end_chunk: str = options.END_CHUNK,
        read_chunk_size: int = options.READ_CHUNK_SIZE,
        keypair: Optional[Union["Ed25519()", Tuple[bytes, bytes]]] = None,
        autoreload: bool = False,
        *args, **kwargs

    ):
        self.user_length = user_length
        self.public_key_length = public_key_length
        self.headers_length = headers_length

        __max_size = max(
            self.user_length, self.public_key_length, self.headers_length

        )

        if (memory_limit < __max_size):
            raise RuntimeError(_("El tamaño de la asignación de la memoria es muy bajo para lo requerido: {}").format(__max_size))

        super().__init__(
            *args,
            max_buffer_size=memory_limit + len(end_chunk),
            read_chunk_size=read_chunk_size,
            **kwargs

        )

        self.end_chunk = end_chunk
        self.memory_limit = memory_limit
        self.utesla_version = utesla_version
        self.pool_object = pool_object
        self.procs = procs
        self.user_server = user_server
        self.init_path = init_path
        self.user_data = user_data
        self.service_file = service_file
        self.index_name = show_services.parse_path(
            os.path.join(service_file, index_name),

        )
        self.admin_service = show_services.parse_path(
            os.path.join(service_file, admin_service)

        )
        self.recv_timeout = recv_timeout
        self.templates_conf = templates
        self.templates = {
            "preface" : self.templates_conf.pop("preface"),
            "intro"   : self.templates_conf.pop("intro"),
            "end"     : self.templates_conf.pop("end")
                
        }

        self.autoreload = autoreload
        self.__exp_func = lambda level: logger.isEnabledFor(level)

        if (keypair is None):
            logger.debug(_("No se han ajustado claves ed25519; generando..."))

            keypair = ed25519.to_raw()

        self.keypair = keypair

    @staticmethod
    def __parse_name(name):
        name = "/%s(/*)$" % (
            re.escape(name)
            
        )

        return name

    def __check(self, path):
        current_handler = None
        Service_tuple = inspect.namedtuple(
            "Service", ("exists", "current_cls", "root_cls")    
            
        )
        try:
            (service_name, sub_service_name) = path[:1].split("/", 1)

        except ValueError:
            (service_name, sub_service_name) = path[1:], ""

        index_name_regex = self.__parse_name(self.index_name)

        index_dirname = "%s/%s" % (self.service_file, self.index_name)
        admin_dirname = "%s/%s" % (self.service_file, self.admin_service)

        if not (os.path.isdir(admin_dirname)):
            logger.debug(_("'%s' no existe y es necesario para usarlo como servicio administrativo"), admin_dirname)

            raise exceptions.RootHandlerNotExists(_("¡El servicio administrativo no se encuentra!"))

        root_handler = show_services.get_module(
            "%s/%s.py" % (admin_dirname, os.path.basename(admin_dirname)),
            self.autoreload
                
        )
        
        if (re.match(r"/(/*)$", path)) or (re.match(index_name_regex, path)):
            index_name = "%s/%s.py" % (index_dirname, os.path.basename(index_dirname))

            if (os.path.isfile(index_name)):
                current_handler = show_services.get_module(
                    index_name,
                    self.autoreload
                        
                )

            else:
                logger.debug(
                    _("'%s' no existe y es el servicio requerido por el usuario, además que también es el índice"),
                    index_name
                    
                )

        else:
            current_dirname = "%s/%s" % (
                self.service_file, path[1:]
                    
            )
            current_dirname = remove_badchars.remove(current_dirname, "/")

            if (os.path.isdir(current_dirname)):
                current_name = "%s/%s.py" % (current_dirname, os.path.basename(current_dirname))

            else:
                current_name = "%s.py" % (current_dirname)

            if (re.match(r"^(.+/){2}.+.py$", current_name)) and (os.path.isfile(current_name)):
                current_handler = show_services.get_module(
                    current_name,
                    self.autoreload
                        
                )

            else:
                logger.debug(
                    _("'%s' no existe y es el servicio requerido por el usuario"),
                    path
                    
                )

        if (current_handler is not None):
            return Service_tuple(True, current_handler, root_handler)

        else:
            return Service_tuple(False, None, root_handler)

    @staticmethod
    async def __init_service(cls, params):
        obj = await parse_args.async_execute_function(cls, params)

        return obj

    def __create_procs(self):
        # Estos procedimientos son usados mientras dure esta sesión
        proc_control_obj = proc_control.ProcControl(
            self.procs.ProcControl.getTarget(), self.procs.ProcControl.getInterval()

        )
        proc_stream_obj = proc_stream.ProcStream()

        procs_local = procs_repr.procedures(proc_control_obj, proc_stream_obj)
        
        # Y para que no haya interferencias, se crea el ámbito entre procedimientos
        # globales y locales.
        procs = procs_repr.proc_scope(procs_local, self.procs)

        return procs

    async def handle_stream(self, stream, address):
        # La excepción será mostrada al final y se usará el nivel de advertencia en vez de información
        exception = None

        (procs_handler, procs_root) = self.__create_procs(), self.__create_procs()

        # Primero iniciamos el contador de usuario y lo pasamos a las plantillas.
        # Si no se pasara se crearía uno implícitamente, lo cual no sería lo
        # deseado, debido que los tiempos pueden ser inexactos.
        user_counter = counter.Counter()

        preface_template = CustomTemplate(
            self.templates.get("preface"),
            user_counter = user_counter,
            **self.templates_conf
            
        )
        intro_template = CustomTemplate(
            self.templates.get("intro"),
            user_counter = user_counter,
            **self.templates_conf
                
        )
        service_template = CustomTemplate(
            self.templates.get("intro"),
            user_counter = user_counter,
            **self.templates_conf
                
        )
        end_template = CustomTemplate(
            self.templates.get("end"),
            user_counter = user_counter,
            **self.templates_conf
                
        )

        control = MainDataControl(**{
            "pool"              : self.pool_object,
            "user_length"       : self.user_length,
            "public_key_length" : self.public_key_length,
            "headers_length"    : self.headers_length,
            "memory_limit"      : self.memory_limit,
            "recv_timeout"      : self.recv_timeout,
            "init_path"         : self.init_path,
            "user_data"         : self.user_data,
            "keypair"           : self.keypair,
            "stream"            : stream,
            "end_chunk"         : self.end_chunk
            
        })
        
        # Ajustamos la dirección IP para una mejor depuración
        control.request.address = address

        # Datos que podría usar el cliente
        control.set_header("version", self.utesla_version, str)
        control.set_header("limit", self.memory_limit, int)
        control.set_header("status_code", 0)
        control.set_header("status", "")

        # Ajustamos los valores para mejorar la depuración
        #
        # Primero el prefacio
        preface_template.set_request(control.request)
        preface_template.set_function_expression(self.__exp_func)

        # Ahora la introducción
        intro_template.set_request(control.request)
        intro_template.set_function_expression(self.__exp_func)

        # La plantilla que se usará en el servicio y tendrá que ser
        # igual a la introducción.
        service_template.set_request(control.request)

        # Y por último el final
        end_template.set_request(control.request)
        end_template.set_function_expression(self.__exp_func)

        # Para informar al administrador que un usuario ha ingresado
        logger.info(preface_template.get_template(logging.INFO))

        gen = control.initialize()

        request_params = {
            "template"              : service_template,
            "headers"               : control.headers,
            "request"               : control.request,
            "pool"                  : self.pool_object,
            "write_function"        : control.write,
            "write_status_function" : control.write_status,
            "body"                  : gen
            
        }

        # Ajustamos primero los procedimientos para el servicio actual.
        request_params["procs"] = self.__create_procs()
        request = RequestController(**request_params)

        # Y luego ajustamos los procedimientos para el servicio administrativo
        # para que no haya interferencias entre los dos.
        request_params["procs"] = self.__create_procs()
        admin_request = RequestController(**request_params)

        try:
            async for body in gen:
                # Sería una perdida de tiempo tener que forzar al cliente a reconectarse por un error
                # sutil que se puede arreglar mandando un código de estado diferente a cero.
                try:
                    # Ajustamos el último dato que el cliente transmitió
                    admin_request.data = body
                    request.data = body

                    logger.info(intro_template.get_template(logging.INFO))

                    # Por seguridad no se usa el servicio administrativo
                    if (re.match(self.__parse_name(self.admin_service), control.request.path)):
                        logger.warning(
                            _("%s: No se puede acceder a este servicio de manera convencional"),
                            intro_template.get_template(logging.WARNING),

                        )

                        await control.write_status(errno.EPERM, _("No se puede acceder a este servicio"))
                        continue

                    control.reset_status()

                    current_status = self.__check(control.request.path)

                    root_handler = await self.__init_service(
                        current_status.root_cls, control.request.init_params
                            
                    )

                    if not (utils.is_admin(root_handler)):
                        logger.error(
                            _("%s: El servicio administrativo no es válido para continuar"),
                            intro_template.get_template(logging.ERROR)

                        )

                        await control.write_status(errno.ESERVER)
                        continue

                    # Ajustamos la información del servicio administrativo
                    utils.set_controller(root_handler, admin_request)

                    if (current_status.exists):
                        # Ajustamos los propiedades y métodos necesarios y permitidos
                        current_handler = await self.__init_service(
                            current_status.current_cls, control.request.init_params
                            
                        )

                        token_required = utils.is_token_required(
                            current_handler,
                            control.request.action,
                            control.request.path
                            
                        )

                        if (token_required):
                            root_access = execute_possible_coroutine.execute(
                                getattr(root_handler, defaults.access_method)
                                
                            )

                            if not (await root_access):
                                continue

                            service_allowed = await utils.is_service_allowed(
                                control.request.token_hash,
                                self.pool_object,
                                control.request.path
                                
                            )

                            if not (service_allowed) and (control.request.is_guest_user):
                                logger.warning(
                                    _("%s: No tiene permitido usar este servicio"),
                                    intro_template.get_template(logging.WARNING)
                                    
                                )

                                await control.write_status(errno.EPERM)
                                continue

                        allowed = utils.is_allowed(current_handler, control.request.path)

                        if not (allowed):
                            logger.warning(
                                _("%s: El servicio no está habilitado por el administrador"),
                                intro_template.get_template(logging.WARNING)

                            )
                            
                            await control.write_status(errno.ENOSRV)
                            continue

                        
                        is_support = utils.is_support_method(
                            current_handler,
                            control.request.action,
                            control.request.path
                            
                        )

                        if not (is_support):
                            logger.warning(
                                _("%s: La acción propuesta no existe o no está habilitada"),
                                intro_template.get_template(logging.WARNING)
                                
                            )

                            await control.write_status(errno.ENOACT)
                            continue

                        # Y ahora ajustamos la información al servicio
                        utils.set_controller(current_handler, request, control.request.path)

                        initializer_method = utils.get_initializer(current_handler)

                        if (initializer_method is None) or (await execute_possible_coroutine.execute(initializer_method)):
                            await parse_args.async_execute_function(
                                getattr(current_handler, control.request.action),
                                control.request.params

                            )

                        else:
                            logger.warning(
                                _("%s: El método inicializador ha impedido continuar con la operación"),
                                intro_template.get_template(logging.WARNING)
                                
                            )

                    else:
                        logger.warning(
                            _("%s: El servicio no existe localmente"),
                            intro_template.get_template(logging.WARNING)
                            
                        )

                        await execute_possible_coroutine.execute(
                            getattr(root_handler, defaults.remote_method)
                            
                        )

                except parse_args.ConvertionException as err:
                    logger.exception(
                        _("%s: Hubo un error convirtiendo los tipos de datos"),
                        intro_template.get_template(logging.ERROR), exc_info=err.exception
                        
                    )

                    await control.write_status(
                        errno.ECLIENT, _("Valor incorrecto para el parámetro: {}").format(err.key)
                        
                    )

                except parse_args.InvalidDataType as err:
                    logger.error(
                        _("%s: El parámetro '%s' no es un tipo de dato válido"),
                        intro_template.get_template(logging.ERROR), err.key 
                        
                    )

                    await control.write_status(errno.ESERVER)

                except parse_args.RequiredArgument as err:
                    logger.error("%s: %s", intro_template.get_template(logging.ERROR), str(err))

                    await control.write_status(errno.ECLIENT, str(err))

                except exceptions.RootHandlerNotExists as err:
                    logger.error("%s: %s", intro_template.get_template(logging.ERROR), str(err))

                    await control.write_status(errno.ESERVER)

        except tornado.iostream.StreamClosedError:
            pass

        except nacl.exceptions.BadSignatureError:
            exception = _("¡La verificación del mensaje no es correcta!")

        except exceptions.PublicKeyNotFound:
            exception = _("¡El usuario '{}' no existe!").format(control.request.real_user)

        except asyncio.TimeoutError:
            exception = _("Ha concluido el tiempo de espera para la recepción de datos")

        except Exception as err:
            logger.exception(_("Excepción captada"))

        finally:
            if (exception is not None):
                logger.warning(
                    "%s: %s",
                    end_template.get_template(logging.WARNING), exception
                        
                )

            else:
                logger.info(end_template.get_template(logging.INFO))

            # Terminamos la conexión
            stream.close()

            # Y terminamos los procesos/sub-procesos
            for p in (request.procs, admin_request.procs):
                try:
                    await p.locals.ProcStream.async_removeall()
                
                except:
                    logging.exception(_("Ocurrió una excepción cerrando los archivos abiertos"))
                
                try:
                    p.locals.ProcControl.setTarget("processes")
                    await p.locals.ProcControl.AsyncClear()

                except:
                    logging.exception(_("Ocurrió una excepción cerrando los procesos aún abiertos"))

def start(lhost: str,
          lport: int,
          *args, **kwargs) -> object:
    logging.info(_("Escuchando en %s:%d"), lhost, lport)

    server = MainHandler(*args, **kwargs)
    server.listen(lport, lhost)

    return server
