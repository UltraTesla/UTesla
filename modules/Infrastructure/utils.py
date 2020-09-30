import re
import time
import copy
import logging
import inspect
import hashlib
import binascii
import asyncio

from typing import Any, Optional, Dict, Tuple, NoReturn, Union, Callable

from modules.Infrastructure import errno
from modules.Infrastructure import parse
from modules.Infrastructure import options
from modules.Crypt import x25519_xsalsa20_poly1305MAC, ed25519
from utils.extra import counter
from utils.extra import parse_args
from utils.extra import create_translation

from config import defaults

_ = create_translation.create("utils")

class MainHeaders:
    """Crea y administra los encabezados"""

    def __init__(self, headers={}):
        self.headers = copy.deepcopy(headers)

    def _add(self, dictionary, key, value, *args, **kwargs):
        value = self._check_type(value, *args, **kwargs)

        if not (key in dictionary):
            dictionary[key] = [value]

        elif (isinstance(dictionary[key], list)):
            dictionary[key].append(value)

        else:
            if not (isinstance(value, list)):
                value = [value]

            dictionary[key] = [dictionary[key]] + value

    @staticmethod
    def _check_type(value, type=None, index=0, convert=True):
        if (isinstance(type, (tuple, list))):
            default_type = type[index]

        else:
            default_type = type

        if (type is not None) and (value is None):
            value = default_type()

        elif (type is not None) and (value is not None):
            try:
                if (convert):
                    value = default_type(value)

                else:
                    if not (isinstance(value, type)):
                        raise TypeError()

            except (ValueError, TypeError):
                raise TypeError(_("Tipo de dato incorrecto"))

        return value

    def set_header(self, key: Any, value: Any, *args, **kwargs) -> None:
        """Ajusta las claves claves de los encabezados
        
        Args:
            key:
              La clave

            value:
              El valor de dicha clave

            *args, **kwargs:
              - type:
                  El tipo de dato que se espera recibir
              - index:
                  Si son muchos (como una lista o una tupla), esto es
                  útil para esclarecer explícitamente cuál es el
                  valor que se desea.

              - convert:
                  Convertir el valor al tipo de dato ajustado en `type`
                  cuando no sea el correcto, o generar una excepción.
        """

        value = self._check_type(value, *args, **kwargs)

        self.headers[key] = value

    def __setitem__(self, key, value):
        self.headers[key] = value

    def del_header(self, key: str, /) -> None:
        """Borrar la clave en el encabezado"""

        self.headers.pop(key)

    __delitem__ = del_header

    def add_header(self, *args, **kwargs) -> None:
        """Ajusta las claves de los encabezados
        
        A diferencia de `set_header()`, este método no reemplaza
        el valor (si existe), en su lugar, lo agrega a una lista.
        """

        self._add(self.headers, *args, **kwargs)

    def get_header(self, key: Any, default: Any = None) -> Any:
        """Obtener el valor de una clave en el encabezado"""

        return self.headers.get(key, default)

    __getitem__ = get_header

class MainParameters(MainHeaders):
    def __init__(self):
        super().__init__()

        self.reset_status()

    def set_status_code(self, code: int, /) -> None:
        super().set_header("status_code", code, int, convert=False)

    def set_status(self, status: str = "", /) -> None:
        super().set_header("status", status, str, convert=False)

    def get_status_code(self, default: int = -1) -> int:
        return int(super().get_header("status_code", default))

    def get_status(self, default: Any = None) -> Optional[str]:
        return super().get_header("status", default)

    def reset_status(self) -> None:
        self.set_status_code(0)
        self.set_status()

class StrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, value in super().items():
            self.__check_type(key)

    @staticmethod
    def __check_type(key):
        if not (isinstance(key, str)):
            raise TypeError(_("La clave '{}' no tiene un tipo de dato correcto").format(key))

    def __setitem__(self, key, value, /):
        self.__check_type(key)

        super().__setitem__(key, value)

class Request(MainParameters):
    """
    Crea un objeto con información sobre la petición actual

    Attributes:
        path:
          La ruta del servicio
        
        action:
          La acción del servicio

        token:
          El token de acceso
        
        params:
          Los parámetros del servicio
        
        init_params:
          Los parámetros para iniciar el servicio
        
        force:
          Forzar al servidor a usar un nodo específico
        
        node:
          El nodo a conectar. Tiene que estar ajustado `force`
          para que haga efecto.
        
        is_packed:
          Usar o no `msgpack`
        
        is_guest_user:
          **True** cuando sea un usuario invitado; **False** cuando no.
        
        address:
          La dirección IP del cliente
    """

    def __init__(
        self,
        user: str = None,
        userid: int = None,
        real_user: bytes = None,
        path: str = "/",
        action: str = None,
        token: str = None,
        params: dict = {},
        init_params: Dict[str, Any] = {},
        force: bool = False,
        address: tuple = (),
        node: tuple = (),
        is_packed: bool = True,
        is_guest_user: bool = True

    ):
        super().__init__()

        self.set_user(user)
        self.set_userid(userid)
        self.set_real_user(real_user)

        self.path = path
        self.action = action
        self.token = token
        self.params = params
        self.init_params = init_params
        self.force = force
        self.node = node
        self.is_packed = is_packed
        self.is_guest_user = is_guest_user
        self.address = address
        self.__user_length = options.USER_LENGTH

        super().set_header("path", self.path, str)
        super().set_header("action", self.action, str)
        super().set_header("token", self.token, str)
        super().set_header("params", self.params)
        super().set_header("init_params", self.init_params)
        super().set_header("force", self.force, bool)
        super().set_header("node", self.node, tuple)
        super().set_header("is_packed", self.is_packed, bool)

    def get_user_length(self) -> int:
        return self.__user_length

    def set_user_length(self, length: int, /) -> None:
        self.__check_type(length, int)

        if (length is None):
            length = 32

        self.__user_length = length

    @property
    def real_user(self) -> bytes:
        return self.__real_user

    def set_real_user(self, real_user: bytes, /) -> None:
        self.__check_type(real_user, bytes)

        if (real_user is not None) and (len(real_user) != self.__user_length):
            raise ValueError(_("Longitud del tamaño del usuario real inválida"))

        self.__real_user = real_user
    
    @property
    def user(self) -> str:
        return self.__user

    def set_user(self, user: str, /) -> None:
        self.__check_type(user, str)

        self.__user = user

    @property
    def userid(self) -> int:
        return self.__userid

    def set_userid(self, userid: int, /) -> None:
        if (userid is not None) and not (isinstance(userid, int)):
            userid = int(userid)

        self.__userid = userid

    @staticmethod
    def __check_type(val, type):
        if (val is not None) and not (isinstance(val, type)):
            raise TypeError(_("El tipo de dato no es válido"))

    def __parse_bool(self, val, /):
        self.__check_type(val, (int, bool))

        return bool(val)

    def __parse_address(self, val, /):
        self.__check_type(val, (tuple, list))
        
        if (val == []) or (val == ()):
            return val

        if (len(val) != 2):
            raise ValueError(_("La estructura de la dirección del nodo no es correcta. Debe ser '(address, port)'"))

        (addr, port) = val

        self.__check_type(addr, str)

        if not (isinstance(port, int)):
            port = int(port)

        if (port <= 0) or (port > 65535):
            raise ValueError(_("El puerto está en un rango no válido"))

        return (addr, port)

    @property
    def path(self) -> str:
        return self.__path

    @path.setter
    def path(self, path: str, /) -> None:
        self.__check_type(path, str)

        if (path is None):
            path = "/"

        else:
            if (path[:1] != "/"):
                path = "/" + path

        self.__path = path

    @property
    def action(self) -> str:
        return self.__action

    @action.setter
    def action(self, action: str, /) -> None:
        self.__check_type(action, str)

        self.__action = action

    @property
    def token(self) -> str:
        return self.__token

    @token.setter
    def token(self, token: str, /) -> None:
        self.__check_type(token, str)

        self.__token = token

        if (token is not None):
            self.__token_hash = hashlib.sha3_256(
                binascii.unhexlify(token)
                    
            ).hexdigest()

        else:
            self.__token_hash = None

    @property
    def token_hash(self) -> str:
        return self.__token_hash

    def __parse_dict(self, dictionary, /):
        self.__check_type(dictionary, dict)

        if (dictionary is None):
            return StrDict()

        else:
            return StrDict(dictionary)

    @property
    def params(self) -> dict:
        return self.__params

    @params.setter
    def params(self, params: dict, /) -> None:
        self.__params = self.__parse_dict(params)

    @property
    def init_params(self) -> Dict[str, Any]:
        return self.__init_params

    @init_params.setter
    def init_params(self, init_params: Dict[str, Any], /) -> None:
        self.__init_params = self.__parse_dict(init_params)

    @property
    def force(self) -> bool:
        return self.__force

    @force.setter
    def force(self, v: bool, /) -> None:
        self.__force = self.__parse_bool(v)

    @property
    def node(self) -> tuple:
        return self.__node

    @node.setter
    def node(self, node: tuple, /) -> None:
        self.__node = self.__parse_address(node)

    @property
    def is_guest_user(self) -> bool:
        return self.__is_guest_user

    def set_guest_user(self, v: bool, /) -> None:
        self.__is_guest_user = self.__parse_bool(v)

    @is_guest_user.setter
    def is_guest_user(self, v: bool, /) -> None:
        self.set_guest_user(v)

    @property
    def is_packed(self) -> bool:
        return self.__is_packed

    @is_packed.setter
    def is_packed(self, v: bool, /) -> None:
        self.__is_packed = self.__parse_bool(v)
    
    @property
    def address(self) -> tuple:
        return self.__address

    @address.setter
    def address(self, address: tuple, /) -> None:
        self.__address = self.__parse_address(address)

class MainCalls(MainParameters):
    def __init__(
        self,
        stream: "tornado.iostream.IOStream",
        keypair: Union[Tuple[bytes, bytes], "Ed25519()"],
        init_path: str = options.INIT_PATH,
        user_data: str = options.USER_DATA,
        request: "Request()" = None,
        end_chunk: int = options.END_CHUNK,
        user_length: int = options.USER_LENGTH
        
    ):
        super().__init__()

        if (request is None):
            request = Request()
            request.set_user_length(user_length)

        self.stream = stream
        self.keypair = keypair
        self.request = request
        self.end_chunk = end_chunk.encode()
        self.parse = None
        self.init_path = init_path
        self.user_data = user_data
        self.__end_length = len(self.end_chunk) # útil para eliminar el separador en los datos recibidos
        # Las claves Curve25519
        self.__keys = None
        # Usado por ambas partes para compartir la clave pública
        self.__shared = True

    async def write_status(
        self,
        code: int,
        status: str = None,
        message: Any = None,
        *args, **kwargs
        
    ) -> None:
        self.set_status_code(code)

        if (status is None):
            status = errno.default_messages.get(code, "")
        
        self.set_status(status)

        await self.write(message, *args, **kwargs)

    async def write(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    async def recv_data(self, size: int, *, timeout: int = None) -> Any:
        fut = self.stream.read_until(self.end_chunk, size + self.__end_length)

        if (timeout is None) or (timeout <= 0):
            result = await fut

        else:
            result = await asyncio.wait_for(
                fut, timeout

            )

        return result[:self.__end_length * -1]

    async def write_data(self, data: Any) -> None:
        await self.stream.write(data + self.end_chunk)

    def generate_ecdh_keys(self, *, replace: bool = False) -> None:
        if (self.__keys is not None) and not (replace):
            return

        self.__keys = x25519_xsalsa20_poly1305MAC.to_raw()

    def set_session(self, key: bytes, /) -> None:
        self.generate_ecdh_keys()
        session = x25519_xsalsa20_poly1305MAC.InitSession(key, self.__keys.private)
        self.parse = parse.Parser(
            session,
            self.keypair.private,
            self.init_path,
            self.user_data
            
        )

    def check_not_defined_session(self) -> NoReturn:
        if (self.parse is None) or (self.__keys is None):
            raise RuntimeError(_("Es necesario definir la sesión"))

    async def shareKey(self, signingKey: bytes = None) -> None:
        if (self.__shared):
            self.__shared = False

            self.generate_ecdh_keys()

            if (signingKey is None):
                signingKey = self.keypair.private

            await self.write_data(
                ed25519.sign(signingKey, self.__keys.public)
                    
            )

class MainClient(MainCalls):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Usado por el cliente para enviar el nombre de usuario al servidor
        self.__initial = True

    async def shareUsername(self, real_user: bytes = None) -> None:
        if (self.__initial):
            self.__initial = False

            if (real_user is None):
                real_user = self.request.real_user

            await self.write_data(real_user)

    async def write(self, data: Any, headers: dict = None, *args, **kwargs) -> None:
        self.check_not_defined_session()

        if (headers is None):
            headers = self.headers

        await self.write_data(
            self.parse.build(headers)
                
        )

        await self.write_data(
            self.parse.build(data, *args, **kwargs)
                
        )

    async def read(self, verifyKey: bytes, size: int, *args, timeout: int = None, **kwargs) -> Any:
        self.check_not_defined_session()

        return self.parse.get_message(
                    await self.recv_data(size, timeout=timeout),
                    verifyKey,
                    *args, **kwargs

               )

class MainServer(MainCalls):
    async def read(self, size: int, *args, timeout: Optional[int] = None, **kwargs) -> Any:
        self.check_not_defined_session()

        return await self.parse.destroy(
                   await self.recv_data(size, timeout=timeout),
                   self.request.real_user,
                   *args, **kwargs

               )

    async def write(self, data: Any, headers: Optional[dict] = None, *args, **kwargs) -> None: 
        self.check_not_defined_session()

        if (headers is None):
            headers = self.headers

        await self.write_data(
            self.parse.reply(headers)

        )

        await self.write_data(
            self.parse.reply(data, *args, **kwargs)
                
        )

def is_support_method(handler: object, action: str, path: str) -> Optional[bool]:
    if not (hasattr(handler, defaults.supported_methods_name)):
        logging.error(_("¡El servicio '%s' no tiene métodos habilitados!"), path)
        return False

    supported_methods = getattr(
        handler, defaults.supported_methods_name

    )

    if (isinstance(supported_methods, (list, tuple))):
        is_supported = action in supported_methods

    elif (isinstance(supported_methods, str)):
        is_supported = action == supported_methods

    else:
        logging.error(_(
            "El tipo de dato de la propiedad que indica qué "
            "métodos están habilitados no es válida en el "
            "servicio '%s'"),
            path
            
        )
        return False

    if (hasattr(handler, action)) and (is_supported):
        return True

    else:
        logging.warning(_(
            "La acción '%s' no existe o no está habilitada en el "
            "servicio '%s'"),
            action, path
            
        )

        return False

def is_allowed(handler: object, path: str) -> object:
    # Es opcional esta propiedad. Por defecto se creerá que el administrador lo desea.
    if not (hasattr(handler, defaults.is_allow_methods_name)):
        return True

    val = getattr(handler, defaults.is_allow_methods_name)

    if (isinstance(val, (int, bool))):
        return val

    else:
        logging.warning(_(
            "El tipo de dato de la propiedad que indica si está o no "
            "habilitado el servicio no es válido para '%s'"),
            path
            
        )

        return True

def is_token_required(handler: object, action: str, path: str) -> bool:
    if not (hasattr(handler, defaults.is_token_required_methods_name)):
        return True

    val = getattr(handler, defaults.is_token_required_methods_name)
    
    if (isinstance(val, (list, tuple))):
        token_required = not action in val

    elif (isinstance(val, str)):
        token_required = action != val

    else:
        logging.warning(_(
            "El tipo de dato de la propiedad que indica qué métodos "
            "requieren de un token no es es válida en el servicio '%s'"),
            path
            
        )
        
        return True

    return token_required

async def is_service_allowed(token: str, pool: object, path: str) -> bool:
    if (path != "/") and (path[:1] == "/"):
        path = path[1:]

    regex = await pool.return_first_result("get_services_allowed", token)

    if (regex is None):
        logging.warning(_(
            "No se pudo obtener la expresión regular que "
            "indica si está o no habilitado este servicio "
            "para el token usado en esta sesión."
            
        ))

        return False

    else:
        (regex,) = regex


    if (re.match(regex, path)):
        return True

    else:
        return False

def _has_params(handler, *, keyword_only=False, return_count=False):
    inspection = parse_args.parse(handler)

    len_args = len(inspection[parse_args.KEYWORD_ONLY])

    if not (keyword_only):
        len_args += len(inspection[parse_args.POSITIONAL_ONLY])
        len_args += len(inspection[parse_args.POSITIONAL_OR_KEYWORD])

    if (return_count):
        return len_args

    else:
        return len_args > 0

def get_initializer(handler: object) -> Callable[[], None]:
    if not (hasattr(handler, defaults.initializer_methods_name)):
        return

    initializer = getattr(handler, defaults.initializer_methods_name)

    if not (callable(initializer)):
        logging.warning(_("¡El inicializador debe poder ser llamado!"))
        
        return

    if (_has_params(initializer)):
        logging.warning(_("El inicializador no debe llevar argumentos"))

        return

    return initializer

def is_admin(handler: object) -> bool:
    if not (hasattr(handler, defaults.access_method)) or \
       not (hasattr(handler, defaults.remote_method)):
        logging.warning(
            _("El servicio administrativo debe tener un método llamado '%s' y uno llamado '%s'"),
            defaults.access_method, defaults.remote_method
            
        )

        return False

    handler_access = getattr(handler, defaults.access_method)
    handler_remote = getattr(handler, defaults.remote_method)

    if not (callable(handler_access)) or not (callable(handler_remote)):
        logging.warning(
            _("¡Tanto el método '%s' como '%s' deben poder ser llamados!"),
            defaults.access_method,
            defaults.remote_method
                
        )

        return False

    # Para ahorrar código usando el operador ternario
    len_access_args = _has_params(handler_access)

    if (len_access_args) or (_has_params(handler_remote)):
        logging.warning(
            _("El método '%s' del servicio administrativo no debe recibir ni argumentos ni argumentos clave"),
            defaults.access_method if (len_access_args) else \
            defaults.remote_method
            
        )

        return False

    return True

def set_controller(handler: object, controller: "RequestController()", path: Optional[str] = None) -> object:
    if (path is None):
        service = _("administrativo")

    else:
        service = "'%s'" % path

    if not (hasattr(handler, defaults.set_controller_methods_name)):
        logging.warning(_("El servicio %s no tiene un método para ajustar los datos"), path)

        return

    handler_controller = getattr(handler, defaults.set_controller_methods_name)

    if not (callable(handler_controller)):
        logging.warning(
            _("¡El método '%s' del servicio %s no se puede llamar!"),
            defaults.set_controller_methods_name, service
            
        )

        return

    if (_has_params(handler_controller, keyword_only=True)):
        logging.warning(
            _("El método '%s' del servicio %s no puede recibir argumentos clave"),
            defaults.set_controller_methods_name,
            service
                
        )

        return

    if (_has_params(handler_controller, return_count=True) != 1):
        logging.warning(
            _("El método '%s' del servicio %s debe recibir un argumento"),
            defaults.set_controller_methods_name,
            service
            
        )

        return

    handler_controller(controller)

class Templates:
    def __init__(
        self,
        null_data: str = "null",
        true_data: str = "true",
        false_data: str = "false",
        user_length: int = options.USER_LENGTH,
        user_counter: Optional["counter.Counter()"] = None,
        *args, **kwargs
        
    ):
        if (user_counter is None):
            user_counter = counter.Counter()
        
        self.__user_counter = user_counter

        self.null = null_data
        self.true = true_data
        self.false = false_data

        self.__request = Request()
        self.__request.set_user_length(user_length)

    @staticmethod
    def __check_type(v, type):
        if not (isinstance(v, type)):
            raise TypeError(_("El tipo de dato no es correcto"))

    @property
    def null(self) -> str:
        return self.__null

    @null.setter
    def null(self, null: str, /) -> None:
        self.__check_type(null, str)

        self.__null = null

    @property
    def true(self) -> str:
        return self.__true

    @true.setter
    def true(self, true: str, /) -> None:
        self.__check_type(true, str)

        self.__true = true

    @property
    def false(self) -> str:
        return self.__false

    @false.setter
    def false(self, false: str, /) -> None:
        self.__check_type(false, str)

        self.__false = false

    @property
    def request(self) -> "Request()":
        return self.__request

    @request.setter
    def request(self, request: "Request()", /) -> None:
        self.__check_type(request, Request)

        self.__request = request

    def set_request(self, request: "Request()") -> None:
        self.request = request

    def __parse_bool(self, v, /):
        if (v):
            return self.true

        else:
            return self.false

    @property
    def information(self) -> dict:
        info = {}

        # El contador de usuario
        info["seconds"] = self.__user_counter.calc_seconds()
        info["minutes"] = self.__user_counter.calc_minutes()
        info["hours"] = self.__user_counter.calc_hours()
        info["days"] = self.__user_counter.calc_days()
        info["weeks"] = self.__user_counter.calc_weeks()

        if (self.request.address == ()):
            info["address"] = self.null
            info["port"] = -1

        else:
            info["address"] = self.request.address[0]
            info["port"] = self.request.address[1]

        info["path"] = self.request.path
        info["action"] = self.request.action or self.null
        info["force"] = self.__parse_bool(self.request.force)
        
        if (self.request.node == []) or (self.request.node == ()):
            info["node_addr"] = self.null
            info["node_port"] = -1

        else:
            info["node_addr"] = self.request.node[0]
            info["node_port"] = self.request.node[1]

        info["username"] = self.request.user or self.null
        info["userid"] = self.request.userid or -1
        
        if (self.request.real_user is None):
            info["real_user"] = self.null

        else:
            info["real_user"] = self.request.real_user

        info["token"] = self.request.token or self.null
        info["is_packed"] = self.__parse_bool(self.request.is_packed)

        return info

    def generate_template(self, template: str, /) -> str:
        template = time.strftime(template)

        return template % self.information
