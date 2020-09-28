import logging
import inspect
import time
import hashlib
import binascii
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Tuple,
    Union,
    Optional

)

import secrets

from utils.extra import execute_possible_coroutine
from utils.extra import create_translation

from modules.Infrastructure import exceptions

_ = create_translation.create("dbConnector")

async def _execute_async_gen(gen):
    async for i in gen:
        return i

async def _return_coroutine(coroutine):
    if (inspect.isasyncgen(coroutine)):
        async for i in coroutine:
            yield i

    else:
        result = await coroutine

        yield result

class SimpleDBConnector(object):
    def __init__(self, pool):
        self.pool = pool

    async def execute(self, function: Callable[..., Any], *args, **kwargs) -> Any:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                result = function(*args, cursor=cur, **kwargs)

                async for i in _return_coroutine(result):
                    yield i

class UserCallback(object):
    @staticmethod
    async def is_guest_user(userid: int, *, cursor) -> bool:
        """Verifica si un usuario determinado es un usuario invitado"""

        await cursor.execute("SELECT guest_user FROM users WHERE id = %s LIMIT 1", (userid,))

        guest_user = await cursor.fetchone()

        if (guest_user is None):
            raise exceptions.UserNotFound(_("El usuario no existe"))

        else:
            (guest_user,) = guest_user

        return bool(guest_user)

    @staticmethod
    async def insert_user(
        user: str,
        password: str,
        token_limit: int = 1,
        guest_user: bool = False,
        *, cursor

    ) -> None:
        """Añade un nuevo usuario
        
        Args:
            user:
              El nombre de usuario

            password:
              La contraseña

            token_limit:
              El límite de token's permitidos

            guest_user:
              **True** si es un usuario invitado; **False** si no.
        """

        logging.debug(_("Creando nuevo usuario: %s"), user)

        user_hash = hashlib.sha3_224(
            user.encode()

        ).hexdigest()

        await cursor.execute(
            "INSERT INTO users(user, password, token_limit, user_hash, guest_user) VALUES (%s, %s, %s, %s, %s)",
            (user, password, token_limit, user_hash, guest_user)

        )

        logging.debug(_("Usuario %s (%s) creado satisfactoriamente"), user, user_hash)

    @staticmethod
    async def hash2user(hash: str, *, cursor) -> Tuple[str]:
        """Obtiene el nombre de usuario a partir del usuario real (o identificador)"""

        await cursor.execute(
            "SELECT user FROM users WHERE user_hash = %s LIMIT 1", (hash,)

        )

        user = await cursor.fetchone()

        return user

    @staticmethod
    async def get_password(userid: int, *, cursor) -> Tuple[str]:
        """Obtiene la contraseña de un usuario determinado"""

        await cursor.execute(
            "SELECT password FROM users WHERE id = %s LIMIT 1", (userid,)

        )

        password = await cursor.fetchone()

        return password

    @staticmethod
    async def change_password(password: str, userid: int, *, cursor) -> None:
        """Cambiar la contraseña"""

        logging.warning(
            _("¡Cambiando la contraseña del usuario con el identificador: ID:%d!"),
            userid
            
        )

        await cursor.execute(
            "UPDATE users SET password=%s WHERE id = %s LIMIT 1", (password, userid)
                
        )

        logging.debug(
            _("Se ha cambiado satisfactoriamente la contraseña del usuario: ID:%d"),
            userid
            
        )

    @staticmethod
    async def change_token_limit(token_limit: int, userid: int, *, cursor) -> None:
        """Cambiar el límite de la cantidad de token's permitidos"""

        await cursor.execute(
            "UPDATE users SET token_limit=%s WHERE id = %s LIMIT 1", (token_limit, userid)
                
        )

    @staticmethod
    async def delete_user(userid: int, *, cursor) -> None:
        """Borrar un usuario"""

        logging.warning(
            _("¡Borrando usuario con el identificador: ID:%d!"),
            userid
            
        )

        await cursor.execute(
            "DELETE FROM users WHERE id = %s", (userid,)

        )

        logging.debug(
            _("El usuario con el identificador '%d' ha sido borrado satisfactoriamente"),
            userid
            
        )

    @staticmethod
    async def extract_userid(user: str, *, cursor) -> int:
        """Obtiene el identificador de usuario a partir del nombre del mismo"""

        await cursor.execute(
            "SELECT id FROM users WHERE user = %s LIMIT 1", (user,)

        )

        userid = await cursor.fetchone()

        return userid

    @staticmethod
    async def show_users(
        limit: int = 0,
        asc: bool = True, *,
        cursor
        
    ) -> AsyncIterator[Tuple[int, str, int, Union[int, bool]]]:
        """Obtiene los usuarios registrados
        
        Args:
            limit:
              El límite de la cantidad de registrar

            asc:
              **True** para mostrarlos de formar ascendente; **False** para
              mostrarlos de formar descendente.

        Returns:
            Un iterador asincrónico con los usuarios registrados
        
        """

        sql = ["SELECT id, user, token_limit, guest_user FROM users ORDER BY id"]
        args = []

        if (asc):
            sql.append("ASC")

        else:
            sql.append("DESC")

        if (limit > 0):
            sql.append("LIMIT %s")
            args.append(limit)


        await cursor.execute(
            " ".join(sql), args

        )

        while (result := await cursor.fetchone()):
            yield result

class TokenCallback(object):
    @staticmethod
    def token2hash(token: str) -> str:
        """
        Convierte un token de acceso en texto plano a un hash válido
        que lo identificado en la base de datos.
        """

        return hashlib.sha3_256(
            binascii.unhexlify(token)
                
        ).hexdigest()

    @staticmethod
    async def get_token(userid: int, limit: int = 0, *, cursor) -> AsyncIterator[str]:
        """Obtiene todos los token's de un usuario determinado"""

        sql = ["SELECT token FROM tokens WHERE id_user = %s"]
        args = [userid]

        if (limit > 0):
            sql.append("LIMIT %s")
            args.append(limit)

        await cursor.execute(
            " ".join(sql), args

        )
        
        while (token := await cursor.fetchone()):
            yield token

    @staticmethod
    async def get_token_limit(userid: int, *, cursor) -> int:
        """Obtener el límite de token's permitidos por un usuario"""

        await cursor.execute(
            "SELECT token_limit FROM users WHERE id = %s LIMIT 1", (userid,)

        )

        token_limit = await cursor.fetchone()

        return token_limit

    @staticmethod
    async def delete_token(token: str, *, cursor) -> None:
        """Borrar un token de acceso"""

        await cursor.execute(
            "DELETE FROM tokens WHERE token = %s", (token,)

        )

    @staticmethod
    async def count_token(userid: int, *, cursor) -> int:
        """Contar cuántos token's de acceso tiene un usuario actualmente"""

        await cursor.execute(
            "SELECT COUNT(id_user) FROM tokens WHERE id_user = %s", (userid,)

        )

        token_number = await cursor.fetchone()

        return token_number

    @staticmethod
    async def change_services(token: str, services: str, *, cursor) -> None:
        """Cambiar los servicios permitidos por un token de acceso"""

        await cursor.execute(
            "UPDATE tokens SET services = %s WHERE token = %s LIMIT 1",
            (services, token)
                
                
        )

    async def __check_token(self, userid, *, cursor):
        (token_limit,) = await self.get_token_limit(userid, cursor=cursor)
        (token_number,) = await self.count_token(userid, cursor=cursor)

        if (token_number > 0) and (token_limit != 0):
            if (token_number >= token_limit):
                raise exceptions.TokenLimitsExceeded(_("Límites de los tokens excedidos"))
    
    @staticmethod
    def __generate_token(token_len):
        token = secrets.token_bytes(token_len)
        hash_token = hashlib.sha3_256(token).hexdigest()

        return (token, hash_token)

    async def renew_token(self, token: str, token_len: int = 32, *, cursor) -> str:
        """Renueva un token de acceso

        En caso de que haya una filtración en la base de datos y se obtengan los
        token's de acceso de las redes (la de los usuarios están protegidas por
        SHA3_256) y/o se desee renovar (o sea cambiar el token de acceso mas no
        cambiar la fecha de expiración).

        Igualmente los token's expiran, aunque ésto lo decide un usuario.
        
        Args:
            token:
              El token de acceso a renovar

            token_len:
              La longitud del nuevo token de acceso

        Returns:
            El nuevo token de acceso
        """

        (new_token, hash_token) = self.__generate_token(token_len)

        logging.debug(_("Renovando token de acceso..."))

        await cursor.execute(
            "UPDATE tokens SET token = %s WHERE token = %s",
            (hash_token, token)
                
        )

        return new_token.hex()

    async def insert_token(
        self,
        userid: int,
        expire: int,
        services: str = "*",
        token_len: int = 32, *,
        cursor
        
    ) -> str:
        """Inserta un nuevo token

        Args:
            userid:
              El identificador de usuario

            expire:
              La fecha de expiración expresada en segundos

            services:
              Una expresión regular que indica qué servicios estarán habilitados

            token_len:
              La longitud del token

        Returns:
            El token de acceso
        
        """

        (token, hash_token) = self.__generate_token(token_len)

        await self.__check_token(userid, cursor=cursor)

        logging.debug(
            _("Creando un nuevo token para el identificador de usuario: ID:%d"),
            userid
                
        )

        await cursor.execute(
            "INSERT INTO tokens(id_user, token, expire, services) VALUES(%s, %s, UNIX_TIMESTAMP() + %s, %s)",
            (userid, hash_token, expire, services)

        )
        
        return token.hex()

    @staticmethod
    async def is_expired(token: str, *, cursor) -> bool:
        """Verifica si un token ha expirado"""

        await cursor.execute(
            "SELECT expire FROM tokens WHERE token = %s LIMIT 1", (token,)

        )

        is_expired = await cursor.fetchone()

        if (is_expired is None):
            raise exceptions.NonExistentToken(_("El token no existe"))

        else:
            (is_expired,) = is_expired

        return is_expired < int(time.time())

    @staticmethod
    async def token_exists(token: str, *, cursor) -> bool:
        """Verifica si un token existe"""

        await cursor.execute(
            "SELECT COUNT(id_user) FROM tokens WHERE token = %s LIMIT 1",
            (token,)

        )

        exists = await cursor.fetchone()

        return bool(*exists)

    @staticmethod
    async def get_services_allowed(token: str, *, cursor) -> Tuple[str]:
        """Obtiene los servicios habilitados por un token determinado"""

        await cursor.execute(
            "SELECT services FROM tokens WHERE token = %s LIMIT 1",
            (token,)
                
        )

        services = await cursor.fetchone()

        return services

class NetworkCallback(object):
    @staticmethod
    async def is_network_exists_for_id(networkid: int, *, cursor) -> bool:
        """Verifica si una red existe a partir de su identificador"""

        await cursor.execute(
            "SELECT COUNT(id_network) FROM networks WHERE id_network = %s",
            (networkid,)
                
        )

        exists = await cursor.fetchone()

        return bool(*exists)

    @staticmethod
    async def get_user_network(networkid: int, *, cursor) -> Tuple[str]:
        """Obtener el nombre de usuario usado en esa red"""

        await cursor.execute(
            "SELECT user FROM networks WHERE id_network = %s LIMIT 1",
            (networkid,)
                
        )

        user = await cursor.fetchone()

        return user

    @staticmethod
    async def insert_network(network: str, token: str, user: str, *, cursor) -> None:
        """Añadir una red"""

        await cursor.execute(
            "INSERT INTO networks(network, token, user) VALUES(%s, %s, %s)",
            (network, token, user)

        )

    @staticmethod
    async def extract_networkid(network: str, *, cursor) -> Tuple[int]:
        """Extraer el identificador de la red"""

        await cursor.execute(
            "SELECT id_network FROM networks WHERE network = %s LIMIT 1", (network,)

        )

        networkid = await cursor.fetchone()

        return networkid

    @staticmethod
    async def get_network_token(networkid: int, *, cursor) -> Tuple[str]:
        """Obtiene el token del nodo"""

        await cursor.execute(
            "SELECT token FROM networks WHERE id_network = %s LIMIT 1",
            (networkid,)

        )

        token = await cursor.fetchone()

        return token

    @staticmethod
    async def id2network(networkid: int, *, cursor) -> Tuple[str]:
        """A partir del identificador, se obtiene la dirección de la red"""

        await cursor.execute(
            "SELECT network FROM networks WHERE id_network = %s LIMIT 1",
            (networkid,)

        )

        network = await cursor.fetchone()

        return network

    @staticmethod
    async def get_networks(
        limit: int = 0,
        asc: bool = True,
        use_options: bool = False,
        *, cursor

    ) -> AsyncIterator[Union[Tuple[int, str, str], Tuple[str]]]:
        """Obtiene las direcciones de los nodos.
        
        Args:
            limit:
              Límite del número de nodos a obtener

            asc:
              Si es **True** el resultado será ascendente, si no, descendente.

            use_options:
              Si es **True** se obtendrá el identificador del nodo, la dirección y
              el token, si no, simplemente la dirección.

        Returns:
            Un iterador asincrónico con las redes obtenidas.
        """

        args = []

        if (use_options):
            sql = ["SELECT id_network, network, token FROM networks ORDER BY id_network"]

            if (asc):
                sql.append("ASC")

            else:
                sql.append("DESC")

            if (limit > 0):
                sql.append("LIMIT %s")
                args.append(limit)

            await cursor.execute(
                " ".join(sql), args

            )

        else:
            await cursor.execute(
                "SELECT network FROM networks"

            )

        while (result := await cursor.fetchone()):
            yield result

    @staticmethod
    async def delete_network(networkid: int, *, cursor) -> None:
        """Borra un nodo"""

        logging.warning(_("¡Borrando la red con el identificador: ID:%d!"), networkid)

        await cursor.execute(
            "DELETE FROM networks WHERE id_network = %s", (networkid,)

        )

        logging.debug(_("La red con el identificador '%d' ha sido borrado satisfactoriamente"), networkid)

class ServiceCallback(object):
    @staticmethod
    async def set_priority(
        identificator: int,
        priority: int, *,
        only_networks: bool = False,
        cursor
        
    ) -> None:
        """Ajusta la prioridad del servicio o los servicios
        
        La prioridad es usada para organizar mejor la jerarquía de los servicios,
        o en pocas palabras, cuando se obtienen todos los servicios, el orden
        dependerá de la prioridad que tengan éstos.

        Por ejemplo, si el servicio '/foo' tiene prioridad '2' y '/bar' tiene prioridad
        '3', este último será obtenido primero, por ende se usará primero.

        Args:
            identificator:
              El identificador del servicio o la red

            priority:
              La prioridad del o los servicios

            only_network:
              Si es **True** se actualizará la prioridad de todos los servicios que le pertenezcan
              a un nodo determinado; si es **False** se actualizará solo al servicio especificado.
        
        """

        sql = ["UPDATE services SET priority = %s"]
        args = [priority]

        if (only_networks):
            sql.append("WHERE id_network = %s")

        else:
            sql.append("WHERE id_service = %s")

        args.append(identificator)

        await cursor.execute(
            " ".join(sql), args
                
        )

    @staticmethod
    async def is_service_exists_for_id(serviceid: int, *, cursor) -> bool:
        """Verifica si un servicio existe utilizando su identificador"""

        await cursor.execute(
            "SELECT COUNT(id_service) FROM services WHERE id_service = %s",
            (serviceid)
            
        )

        exists = await cursor.fetchone()

        return bool(*exists)

    @staticmethod
    async def insert_service(
        networkid: int,
        service_name: str,
        priority: int = 0,
        *, cursor
        
    ) -> None:
        """Añade un servicio"""

        await cursor.execute(
            "INSERT INTO services(id_network, service, priority) VALUES (%s, %s, %s)",
            (networkid, service_name, priority)

        )

    @staticmethod
    async def service2id(service_name: str, *, cursor) -> AsyncIterator[int]:
        """Obtiene el identificador del nodo si tiene un servicio específico"""

        await cursor.execute(
            "SELECT id_network FROM services WHERE service = %s ORDER BY priority DESC",
            (service_name,)

        )

        while (networkid := await cursor.fetchone()):
            yield networkid

    async def service2net(
        self,
        service_name: str,
        show_ids: bool = False, *,
        cursor
        
    ) -> AsyncIterator[Union[Tuple[int, str], Tuple[str]]]:
        """Obtiene todas las redes que tienen un servicio específico
        
        Args:
            service_name:
              El nombre del servicio

            show_ids:
              **True** para mostrar además la dirección de la red, el identificador de éste;
              **False** para mostrar solo la dirección.

        Returns:
            Un iterador asincrónico con las redes obtenidas
        """

        ids = self.service2id(
            service_name, cursor=cursor

        )

        async for networkid in ids:
            network = await self.id2network(*networkid, cursor=cursor)

            if (show_ids):
                yield networkid + network

            else:
                yield network

    @staticmethod
    async def network_in_service(networkid: int, serviceid: int, *, cursor) -> bool:
        """Verifica si el servicio es parte de un nodo"""

        await cursor.execute(
            "SELECT COUNT(id_network) FROM services WHERE id_service = %s AND id_network = %s LIMIT 1",
            (serviceid, networkid)

        )

        exists = await cursor.fetchone()

        return bool(*exists)

    @staticmethod
    async def get_services(
        limit: int = 0, *,
        only: Optional[int] = None,
        basic: bool = True,
        cursor
        
    ) -> AsyncIterator[Union[Tuple[str, int], Tuple[int, int, str, int]]]:
        """Obtiene los servicios
        
        Obtiene los servicios remotos registrados de otras redes de confianza

        Args:
            limit:
              El límite de registros a obtener

            only:
              Cuando ``basic`` es **False** ``only`` es usado para obtener todos
              los servicios de un nodo específico.

            basic:
              Si ``basic`` es **True** se obtiene sólo el servicio y el tiempo de
              modificación.

        Returns:
            Un iterador asincrónico con los servicios obtenidos
        
        """

        if (basic):
            await cursor.execute(
                "SELECT service FROM services"

            )

        else:
            sql = ["SELECT id_service, id_network, service, priority FROM services"]
            args = []

            if (only is not None):
                networkid = int(only)

                sql.append("WHERE id_network = %s")
                args.append(networkid)

                if (limit > 0):
                    sql.append("LIMIT %s")
                    args.append(int(limit))

            await cursor.execute(
                " ".join(sql), args
                    
            )

        while (result := await cursor.fetchone()):
            yield result

    @staticmethod
    async def net2services(networkid: int, *, cursor) -> AsyncIterator[str]:
        """Obtiene los nombres de los servicios que les pertenezcan a un nodo"""

        await cursor.execute(
            "SELECT service FROM services WHERE id_network = %s",
            (networkid,)

        )

        while (service := await cursor.fetchone()):
            yield service

    @staticmethod
    async def extract_serviceid(service_name: str, *, cursor) -> Tuple[int]:
        """Extrae el identificador del servicio"""

        await cursor.execute(
            "SELECT id_service FROM services WHERE service = %s LIMIT 1",
            (service_name,)

        )

        id_service = await cursor.fetchone()

        return id_service

class Callback(UserCallback, TokenCallback, NetworkCallback, ServiceCallback):
    pass

class UTeslaConnector(SimpleDBConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = Callback()

    async def execute_command(self, function_name: str, *args, **kwargs) -> Any:
        """Ejecutar un comando para modificar u obtener un dato de la base de datos
        
        Args:
            function_name:
              El nombre de la función

            *args:
              Argumentos variables para la función a ejecutar

            **kwargs:
              Argumentos claves variables para la función a ejecutar

        Returns:
            El resultado (si es que tiene) de la función ejecutada
        """

        if not (hasattr(self.callback, function_name)):
            raise RuntimeError(_("La función a llamar no se encuentra"))

        result = self.execute(
            getattr(self.callback, function_name), *args, **kwargs

        )

        async for i in _return_coroutine(result):
            yield i

    async def return_first_result(self, *args, **kwargs):
        """Retorna el primer y sólo el primer resultado

        Este método es igual que `execute_command()` pero sólo retorna el
        primer resultado.
        """

        return await _execute_async_gen(
            self.execute_command(*args, **kwargs)

        )
