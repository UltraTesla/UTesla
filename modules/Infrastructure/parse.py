import os
import logging
from typing import Optional, Union

import aiofiles

from modules.Infrastructure import exceptions

from utils.Crypt import hibrid
from utils.extra import create_translation
from utils.General import parse_config

translation_config = parse_config.parse()["Languages"]

_ = create_translation.create(
    "parser",
    translation_config["localedir"],
    translation_config["language"]
        
)

class Parser:
    """
    Crea la infraestructura de UTesla

    Attributes:
        session: La sesión ECDH
        user_dir: El directorio de las claves de los usuarios
        local_key: La clave de firmado del remitente
    
    """

    def __init__(
        self,
        session: "x25519_xsalsa20_poly1305MAC.InitSession",
        local_key: bytes,
        init_path: str = "data",
        user_dir: str = "pubkeys"

    ):
        """
        Args:
            session:
              La sesión ECDH

            local_key:
              La clave de firmado del remitente

            init_path:
              El prefijo de `user_dir` y `serv_dir` que indica el directorio raíz

            user_dir:
              El directorio de las claves de los usuarios
        """

        self.session = session
        self.user_dir = "%s/%s" % (
            init_path, user_dir
        
        )
        self.local_key = local_key

    @staticmethod
    def __check_length(username):
        user_length = len(username)

        if (user_length != 28) and (user_length != 56):
            raise exceptions.InvalidRequest(_("Identificador de usuario inválido"))

    def __user2hex(self, user):
        self.__check_length(user)

        if (isinstance(user, bytes)):
            user = user.hex()

        elif (isinstance(user, str)):
            user = os.path.basename(user)

        else:
            raise TypeError(_("Tipo de dato del usuario inválido"))

        # Como se modificó su longitud, puede que tenga errores, por lo
        # que se debe volver a verificar.
        self.__check_length(user)

        return user

    @staticmethod
    def __check_key(key_path):
        if not (os.path.isfile(key_path)):
            raise exceptions.PublicKeyNotFound(
                _("Error, la clave '{}' no existe").format(key_path)

            )

    def reply(
        self,
        message: bytes,
        *args, **kwargs

    ) -> bytes:
        """Cifra ``message`` para responder al usuario.

        Esta es la contraparte de `get_message()`

        Args:
            message:
              El mensaje a cifrar

            *args:
              Los argumentos variables para `hibrid.encrypt()`

            **kwargs:
              Los argumentos claves variables para `hibrid.encrypt()`

        Returns:
            Los datos cifrados y firmados
        """

        return hibrid.encrypt(
                    self.local_key,
                    self.session.destination,
                    self.session.source.private,
                    message,
                    *args, **kwargs

               )

    async def destroy(
        self,
        message: bytes,
        real_user: Union[str, bytes],
        *args, **kwargs

    ) -> bytes:
        """Descifra la petición del usuario.

        Esta es la contraparte de `build()`

        Args:
            message:
              El mensaje a descifrar

            real_user:
              El identificador de usuario. Si es un tipo ``bytes`` se convierte
              a una cadena hexadecimal. La longitud no puede ser diferente a
              28 o 56 digitos.

            *args:
              Argumentos variables para `hibrid.decrypt()`

            **kwargs:
              Argumentos variables para `hibrid.decrypt()`

        Returns:
            Los datos descifrados y verificados
        """

        real_user = self.__user2hex(real_user)

        key_path = os.path.join(self.user_dir, real_user)

        self.__check_key(key_path)

        async with aiofiles.open(key_path, "rb") as fd:
            verify_key = await fd.read()

        logging.debug(_("Descifrando datos del identificador '%s'..."), real_user)

        return hibrid.decrypt(
                    verify_key,
                    self.session.destination,
                    self.session.source.private,
                    message,
                    *args, **kwargs

               )

    def build(
        self,
        message: bytes,
        *args, **kwargs

    ) -> bytes:
        """Cifra para realizar una petición al servidor.
        
        Esta es la contraparte de `destroy()`

        Args:
            message:
              El mensaje a cifrar

            signing_key:
              La clave de firmado

            *args:
              Argumentos variables para `hibrid.encrypt()`

            **kwargs:
              Argumentos claves variables para `hibrid.encrypt()`

        Returns:
            Los datos cifrados y firmados
        """

        return hibrid.encrypt(
                   self.local_key,
                   self.session.destination,
                   self.session.source.private,
                   message,
                   *args, **kwargs

               )

    def get_message(
        self,
        data: bytes,
        verify_key: bytes,
        *args, **kwargs

    ) -> bytes:
        """Descifra la respuesta del servidor.

        Esta es la contraparte de `reply()`

        Args:
            data:
              Los datos a descifrar

            verify_key:
              La clave de verificación

        Returns:
            Los datos descifrados y verificados
        """

        return hibrid.decrypt(
                    verify_key,
                    self.session.destination,
                    self.session.source.private,
                    data,
                    *args, **kwargs

               )
