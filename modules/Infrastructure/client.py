import logging
import hashlib
import asyncio

from typing import Optional, Any, Tuple, Union, Dict

import aiofiles
import tornado.tcpclient
import tornado.iostream

from modules.Crypt import x25519_xsalsa20_poly1305MAC
from modules.Crypt import ed25519
from modules.Infrastructure import options
from modules.Infrastructure import utils
from utils.extra import create_translation

from utils.General import parse_config

config = parse_config.parse()

_ = create_translation.create("client")

class UTeslaStreamControl(utils.MainClient):
    def __init__(
        self,
        user: str,
        public_key_length: int = options.PUBLIC_KEY_LENGTH,
        headers_length: int = options.HEADERS_LENGTH,
        memory_limit: int = options.MEMORY_LIMIT,
        *args, **kwargs

    ):
        """Inicia el controlador de flujo

        Inicia el controlador de flujo para el intercambio de datos entre
        el cliente y el servidor.

        Args:
            user:
              El nombre de usuario

            public_key_length:
              El tamaño máximo de la clave pública del servidor

            headers_length:
              El tamaño máximo de los encabezados

            memory_limit:
              El tamaño máximo de la recepción de datos y el almacenamiento en memoria
        """

        super().__init__(*args, **kwargs)

        self.memory_limit = memory_limit
        self.headers_length = headers_length
        self.public_key_length = public_key_length
        self.__server_ecdh_key = None
        self.__server_key = None

        self.request.set_real_user(
            hashlib.sha3_224(user.encode()).digest()

        )

        if not ("params" in self.headers):
            self.headers["params"] = utils.StrDict()

        if not ("init_params" in self.headers):
            self.headers["init_params"] = utils.StrDict()

        self.params = self.headers["params"]
        self.init_params = self.headers["init_params"]

    def set_server_key(self, key: bytes, /) -> None:
        """Ajusta la clave de verificación Ed25519 del servidor"""

        self.__server_key = key

    def __set_headers(self, data):
        # Si no es un diccionario, por lo tanto, escabezados inválidos
        if not (isinstance(data, dict)):
            return

        self.request.headers.update(data)

        self.request.set_status_code(data.get("status_code", -1))
        self.request.set_status(data.get("status"))

    def __reverse_bool(self, key, val):
        val = super().get_header(key, val)
        new_val = not val

        super().set_header(key, new_val, bool)

        return new_val

    def set_force(self) -> bool:
        """Ajusta el forzamiento de un nodo específico de la red

        Returns:
            Si ``force`` por defecto era **False** (o **None**), se actualizará y
            retornará **True**; viceversa si se vuelve a llamar.
        """

        return self.__reverse_bool("force", False)

    def set_node(self, addr: str, port: int) -> None:
        """Ajusta el nodo de la red

        Este método a su vez debe ser usado con `set_force` ya que debe estar en
        **True** para que el servidor puede hacerle caso.
        
        """

        super().set_header("node", (addr, port))

    def del_node(self) -> None:
        """Borra el nodo ajustado con `set_node`"""

        super().set_header("node", ())

    def set_packed(self) -> bool:
        """Usar o no `msgpack` para el intercambio de datos.
         
        Es recomendable deshabilitarlo cuando se transfieran archivos o realmente
        no se tenga que usar todas las funcionalidades que provee `msgpack` ya que
        aumentaría el rendimiento, pero todo dependerá del servicio y el cliente mismo.

        Returns:
            Si ``is_packed`` por defecto era **True** (o **None**), se actualizará y
            retornará **False**; viceversa si se vuelve a llamar.
        """

        return self.__reverse_bool("is_packed", True)

    def set_init_parameter(self, key: Any, value: Any, /, *args, **kwargs) -> None:
        """Ajusta los parámetros iniciales
        
        Algunos servicios pueden requerir ajustar valores antes de usar sus acciones,
        por lo que este método se encargaría de eso.

        Args:
            key:
              La clave o el nombre del parámetro

            value:
              El valor o argumento del parámetro

            *args:
              Argumentos variables para `set_header()`

            **kwargs:
              Argumentos claves variables para `set_header()`
        """

        super().get_header("init_params")[key] = self._check_type(value, *args, **kwargs)

    def del_init_parameter(self, key: Any, /) -> None:
        """Borra una clave o un parámetro inicial"""

        super().get_header("init_params").pop(key)

    def add_init_parameter(self, *args, **kwargs) -> None:
        """Ajusta parámetros iniciales
        
        La diferencia entre `set_init_parameter` es que los valores son agregados como
        una lista en vez de ser reemplazados.

        Args:
            *args:
              Argumentos variables para `set_header()`

            **kwargs:
              Argumentos claves variables para `set_header()`
        """

        self._add(
            super().get_header("init_params"), *args, **kwargs

        )

    def get_init_parameter(self, key: Any) -> Any:
        """Obtener el valor de una clave o parámetro inicial ya ajustado
        
        Raises:
            KeyError: Cuando el nombre del parámetro inicial no existe
        """

        return super().get_header("init_params")[key]

    def set_parameter(self, key: Any, value: Any, /, *args, **kwargs) -> None:
        """Ajusta parámetros

        Args:
            key:
              La clave o el nombre del parámetro

            value:
              El valor o argumento del parámetro

            *args:
              Argumentos variables para `set_header()`

            **kwargs:
              Argumentos claves variables para `set_header()`
        
        """

        super().get_header("params")[key] = self._check_type(value, *args, **kwargs)

    def del_parameter(self, key: Any, /) -> None:
        """Borra una clave o parámetro"""

        super().get_header("params").pop(key)

    def add_parameter(self, *args, **kwargs) -> None:
        """Ajusta parámetros
        
        La diferencia entre `set_parameter` es que los valores son agregados como
        una lista en vez de ser reemplazados.

        Args:
            *args:
              Argumentos variables para `set_header()`

            **kwargs:
              Argumentos claves variables para `set_header()`
        """

        self._add(
            super().get_header("params"), *args, **kwargs

        )

    def get_parameter(self, key: Any) -> Any:
        """Obtener el valor de una clave o parámetro ya ajustado
        
        Raises:
            KeyError: Cuando el nombre del parámetro no existe
        """

        return super().get_header("params")[key]

    def set_path(self, path: str, action: str, /) -> None:
        """Ajustar el servicio y la acción

        Args:
            path:
              El nombre del servicio (debe comenzar con '/')

            action:
              El nombre de la acción

        Raises:
            TypeError: Cuando el nombre del servicio y/o la acción no sean un string
        """

        super().set_header("path", path, str, convert=False)
        super().set_header("action", action, str, convert=False)

    def get_path(self) -> Tuple[Optional[str], Optional[str]]:
        """Obtener el nombre del servicio y la acción
        
        Returns:
            Una tupla con el nombre del servicio y la acción.
        """

        return (super().get_header("path"), super().get_header("action"))

    def set_token(self, token: str, /) -> None:
        """Ajusta el token de acceso"""

        super().set_header("token", token, str, convert=False)

    def get_token(self) -> Optional[str]:
        """Obtiene el token acceso ajustado"""

        return super().get_header("token")

    async def __shareData(self):
        if (self.__server_ecdh_key is not None):
            return

        await self.shareUsername()
        await self.shareKey()

        self.__server_ecdh_key = ed25519.verify(
            self.__server_key,
            await self.recv_data(self.public_key_length)
            
        )
        self.set_session(
            self.__server_ecdh_key

        )

    async def write(self, *args, **kwargs):
        """Envía datos al servidor"""

        await self.__shareData()
        await super().write(*args, **kwargs)

    async def read(self, *args, **kwargs):
        """Lee datos que envió el servidor"""

        if (self.__server_key is None):
            raise RuntimeError(_("La clave pública del servidor aún no ha sido definida"))

        await self.__shareData()

        self.__set_headers(
            await super().read(self.__server_key, self.headers_length)
                
        )

        return await super().read(
            self.__server_key,
            self.memory_limit,
            *args, **kwargs
            
        )

class UTeslaClient(tornado.tcpclient.TCPClient):
    async def connect(
        self,
        host: str,
        port: int,
        timewait: Optional[int] = None,
        retry: Optional[int] = None,
        *args, **kwargs

    ) -> "tornado.iostream.IOStream":
        """Conectar a un servidor
        
        Args:
            host:
              La dirección a conectar

            port:
              El puerto

            timewait:
              El tiempo de espera para reconectar en caso de fallar.
              Si no se especifica, se usa el valor ajustado en el
              archivo de configuración.

            retry:
              El número total de reintentos.
              Si no se especifica, se usa el valor ajustado en el
              archivo de configuración.

        Returns:
            Retornado un stream (tornado.iostream.IOStream) para controlar
            el envío/recepcion de los datos.

        Raises:
            tornado.iostream.StreamClosed: En caso de no puder conectar
        """

        if (timewait is None):
            timewait = config["Client"]["connect_timewait"]

        if (retry is None):
            retry = config["Client"]["connect_retry"]

        for i in range(1, retry + 1):
            try:
                stream = await super().connect(
                    host, port, *args, **kwargs

                )

            except tornado.iostream.StreamClosedError:
                logging.warning(
                    _("Reintento %d de %d para volver a intentar conectar con %s:%d en %d segundos"),
                    i, retry, host, port, timewait

                )

                if (i == retry):
                    raise

                else:
                    await asyncio.sleep(timewait)

            else:
                return stream

async def simple_client(
    host: str,
    port: int,
    user: str,
    server_key: bytes,
    timewait: Optional[int] = None,
    retry: Optional[int] = None,
    public_key: Optional[bytes] = None,
    private_key: Optional[bytes] = None,
    max_buffer_size: Optional[int] = None,
    uteslaclient: Optional[Union[object, "tornado.tcpclient.TCPClient"]] = None,
    params: Dict[str, Any] = {},
    *args, **kwargs

) -> Tuple["UTeslaStreamControl", Optional[Union[object, "tornado.tcpclient.TCPClient"]], "tornado.iostream.IOStream"]:
    """Facilita ser un cliente

    Esta función provee facilidad en la configuración de parámetros
    del cliente, lo cual ahorra tiempo y esfuerzo.

    Args:
        host:
          La dirección a conectar

        port:
          El puerto

        server_key:
          La clave de verificación Ed25519 del servidor

        timewait:
          El tiempo de espera para reconectar en caso de fallar.
          Si no se especifica, se usa el valor ajustado en el
          archivo de configuración.

        retry:
          El número total de reintentos.
          Si no se especifica, se usa el valor ajustado en el
          archivo de configuración.

        public_key:
          La clave de verificación del usuario-cliente

        private_key:
          La clave de firmado del usuario-cliente

        max_buffer_size:
          El tamaño máximo de la recepción de datos y el almacenamiento en memoria

        uteslaclient:
          Un objeto `tornado.tcpclient.TCPClient` o derivado de éste.
          Si se usa un objeto diferente a UTeslaClient, `timewait` y `retry` se ignoran.

        params:
          Parámetros para la corutina `connect` en `tornado.tcpclient.TCPClient`
          o derivado de éste.

        *args:
          Argumentos variables para `UTeslaStreamControl`

        **kwargs:
          Argumentos claves variables para `UTeslaStreamControl`

    Returns:
        Una tupla con un objeto `ÙTeslaStreamControl`, `tornado.iostream.IOStream`
        y `tornado.tcpclient.TCPClient` ya configurados.
    """

    if (uteslaclient is None):
        uteslaclient = UTeslaClient()

    tcpclient = uteslaclient

    # En caso de que las claves de usuario no sean definidas, se usan
    # la del servidor (pretendiendo que sé es el servidor), ya que hay
    # que recordar que el servidor también hace peticiones a otros nodos
    # de la red.
    if (public_key is None):
        async with aiofiles.open(config["Server"]["pub_key"], "rb") as fd:
            public_key = await fd.read()

    if (private_key is None):
        async with aiofiles.open(config["Server"]["priv_key"], "rb") as fd:
            private_key = await fd.read()

    if (max_buffer_size is None):
        max_buffer_size = config["Client"]["max_buffer_size"]

    # Estos parámetros son válidos para UTeslaClient
    if (isinstance(tcpclient, UTeslaClient)):
        params["timewait"] = timewait
        params["retry"] = retry

    stream = await tcpclient.connect(
        host,
        port,
        max_buffer_size = max_buffer_size,
        **params

    )

    UControl = UTeslaStreamControl(
        user,
        *args, **kwargs,
        stream = stream,
        keypair = ed25519.import_keys(
            public_key, private_key

        ),
        memory_limit = max_buffer_size

    )

    UControl.set_server_key(server_key)

    return (UControl, tcpclient, stream)
