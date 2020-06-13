import logging
import secrets
import time
import hashlib

from modules.Infrastructure import exceptions

READ = 1
WRITE = 2

def _check_null_func(data):
    return data[0][0] if (data) else None

def _check_null(func):
    async def decorate(*args, **kwargs):
        data = await func(*args, **kwargs)

        return _check_null_func(data)

    return decorate

def _is_exists_func(data):
    is_exists = data[0][0]

    return is_exists > 0

def _is_exists(func):
    async def decorate(*args, **kwargs):
        data = await func(*args, **kwargs)

        return _is_exists_func(data)

    return decorate

class UTeslaConnector:
    def __init__(self, pool):
        self.pool = pool

    async def _acquire(self, sql, args=(), cmd=WRITE):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                result = await self._execute(
                    conn, cursor, sql, cmd, args

                )

        return result

    async def _execute(self, conn, cursor, sql, cmd, args=()):
        await cursor.execute(sql, args)

        if (cmd == READ):
            return await cursor.fetchall()

        else:
            logging.debug('¡Datos escritos en la base de datos con éxito!')

    @_check_null
    async def hash2user(self, hash):
        return await self._acquire(
            'SELECT user FROM users WHERE user_hash = %s LIMIT 1', (hash,), cmd=READ

        )

    async def insert_user(self, user,
                                password,
                                token_limit=1):
        logging.debug('Creando nuevo usuario: %s', user)

        user_hash = hashlib.sha3_224(
            user.encode()

        ).hexdigest()

        await self._acquire(
                'INSERT INTO users(user, password, token_limit, user_hash) VALUES (%s, %s, %s, %s)',
            (user, password, token_limit, user_hash)

        )

    @_check_null
    async def get_password(self, userid):
        return await self._acquire(
            'SELECT password FROM users WHERE id = %s LIMIT 1', (userid,), cmd=READ

        )

    @_check_null
    async def count_token(self, userid):
        return await self._acquire(
            'SELECT COUNT(id_user) FROM tokens WHERE id_user = %s', (userid,), cmd=READ

        )

    async def delete_user(self, userid):
        logging.warning('¡Borrando usuario con el identificador: ID:%d!', userid)

        await self._acquire(
            'DELETE FROM users WHERE id = %s', (userid,)

        )

    @_check_null
    async def extract_userid(self, user):
        return await self._acquire(
            'SELECT id FROM users WHERE user = %s LIMIT 1', (user,), cmd=READ
            
        )

    async def get_token(self, userid, limit=0):
        sql = ['SELECT token FROM tokens WHERE id_user = %s']
        args = [userid]

        if (limit > 0):
            sql.append('LIMIT %s')
            args.append(limit)

        return await self._acquire(
                ' '.join(sql), args, cmd=READ

        )

    @_check_null
    async def get_token_limit(self, userid):
        return await self._acquire(
            'SELECT token_limit FROM users WHERE id = %s LIMIT 1', (userid,), cmd=READ

        )

    async def delete_token(self, token):
        logging.debug('Borrando token: %s' % (token))

        await self._acquire(
            'DELETE FROM tokens WHERE token = %s', (token,)

        )

    async def insert_token(self, userid, expire, token_len=32):
        token = secrets.token_hex(token_len)

        token_limit = await self.get_token_limit(userid)
        token_number = await self.count_token(userid)

        # Se usa el operador relacional de igualdad '==' en
        # vez de 'not' para evitar comportamientos raros cuando
        # el administrador puso el límite en 0 (infinito).
        if (token_number > 0) and not (token_limit == 0):
            if (token_number >= token_limit):
                raise exceptions.TokenLimitsExceeded('Límites de los tokens excedidos')

        logging.debug('Creando un nuevo token para el identificador de usuario: ID:%d', userid)

        await self._acquire(
            'INSERT INTO tokens(id_user, token, expire) VALUES(%s, %s, UNIX_TIMESTAMP() + %s)',
            (userid, token, expire)

        )
        
        return token

    async def is_expired(self, token):
        result = await self._acquire(
            'SELECT expire FROM tokens WHERE token = %s LIMIT 1', (token,), cmd=READ

        )

        is_expired = _check_null_func(result)

        if not (is_expired):
            raise exceptions.NonExistentToken('El token no existe')

        return is_expired < int(time.time())

    @_is_exists
    async def token_exists(self, token):
        return await self._acquire(
            'SELECT COUNT(id_user) FROM tokens WHERE token = %s LIMIT 1',
            (token,),
            cmd=READ

        )

    async def show_users(self, limit=0, asc=True):
        sql = ['SELECT id, user, token_limit FROM users ORDER BY id']
        args = []

        if (asc):
            sql.append('ASC')

        else:
            sql.append('DESC')

        if (limit > 0):
            sql.append('LIMIT %s')
            args.append(limit)

        result = await self._acquire(
            ' '.join(sql), args, cmd=READ

        )

        return result

    async def insert_network(self, network, token):
        await self._acquire(
            'INSERT INTO networks(network, token) VALUES(%s, %s)', (network, token)

        )

    @_check_null
    async def extract_networkid(self, network):
        return await self._acquire(
            'SELECT id_network FROM networks WHERE network = %s LIMIT 1', (network,), cmd=READ
            
        )

    @_check_null
    async def get_network_token(self, networkid):
        return await self._acquire(
            'SELECT token FROM networks WHERE id_network = %s LIMIT 1',
            (networkid,),
            cmd=READ

        )

    async def insert_service(self, networkid, service_name, mtime):
        await self._acquire(
            'INSERT INTO services(id_network, service, mtime) VALUES (%s, %s, %s)',
            (networkid, service_name, mtime)

        )

    async def update_service_mtime(self, serviceid, mtime):
        await self._acquire(
            'UPDATE services SET mtime = %s WHERE id_service = %s',
            (mtime, serviceid,)

        )

    @_check_null
    async def get_service_mtime(self, networkid):
        return await self._acquire(
            'SELECT mtime FROM services WHERE id_network = %s',
            (networkid,),
            cmd=READ

        )

    @_check_null
    async def id2network(self, networkid):
        return await self._acquire(
            'SELECT network FROM networks WHERE id_network = %s LIMIT 1',
            (networkid,),
            cmd=READ

        )

    async def service2id(self, service_name):
        return await self._acquire(
            'SELECT id_network FROM services WHERE service = %s',
            (service_name,),
            cmd=READ

        )

    async def service2url(self, service_name, show_ids=False):
        ids = await self.service2id(service_name)

        for id_network in ids:
            network = await self.id2network(id_network)

            if (show_ids):
                yield (id_network, network)

            else:
                yield network

    async def get_services(self):
        return await self._acquire(
            'SELECT service, mtime FROM services',
            cmd=READ

        )

    async def url2services(self, networkid):
        return await self._acquire(
            'SELECT service FROM services WHERE id_network = %s',
            (networkid,),
            cmd=READ

        )

    @_check_null
    async def extract_serviceid(self, service_name):
        return await self._acquire(
            'SELECT id_service FROM services WHERE service = %s',
            (service_name,),
            cmd=READ

        )

    async def get_networks(self):
        return await self._acquire(
            'SELECT network FROM networks',
            cmd=READ

        )
