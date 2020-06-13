import tornado.httpclient
import tornado.httputil
import aiofiles

from modules.Infrastructure import parse
from modules.Crypt import rsa

class UTeslaClient:
    def __init__(self,
                 username,
                 rsa_user=None,
                 rsa_server=None,
                 *args,
                 **kwargs):

        if (rsa_server is not None):
            self.rsa_server = rsa_server

        else:
            self.rsa_server = rsa.Rsa()

        if (rsa_user is not None):
            self.rsa_user = rsa_user

        else:
            self.rsa_user = rsa.Rsa()

        self.parse_user = parse.Parser(
            rsa_object=self.rsa_user

        )

        self.fast_httpclient = tornado.httpclient.AsyncHTTPClient()
        self.username = username
        self.headers = {
            'Content-Type' : 'application/octet-stream'

        }

    async def set_server_key(self, publicKey):
        async with aiofiles.open(publicKey, 'rb') as fd:
            aux = await fd.read()

        self.rsa_server.import_public_key(aux)

    async def set_user_keys(self, publicKey, privateKey):
        async with aiofiles.open(publicKey, 'rb') as fd:
            aux = await fd.read()
            
        self.rsa_user.import_public_key(aux)

        async with aiofiles.open(privateKey, 'rb') as fd:
            aux = await fd.read()

        self.rsa_user.import_private_key(aux)

    def __encrypt(self, cmd):
        return self.parse_user.build(
            self.username, cmd, self.rsa_server.export_public_key()

        )

    def set_headers(self, headers):
        self.headers = headers

    def get_message(self, message):
        if (message):
            return self.parse_user.get_message(
                self.rsa_server.export_public_key(),
                message

            )

        else:
            return message

    async def fetch(self, request, cmd={}, method='POST', **kwargs):
        return await self.fast_httpclient.fetch(
            request,
            body=self.__encrypt(cmd),
            allow_nonstandard_methods=True,
            headers=self.headers,
            method=method,
            **kwargs

        )

class CoreClient(UTeslaClient):
    def __init__(self, url, *args, token=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.url = url
        self.token = token
        self.options = {}
        self.method = 'POST'

    async def _super_fetch(self, cmd):
        return await super().fetch(
            self.url, cmd, self.method, **self.options

        )

    def set_option(self, key, value):
        self.options[key] = value

    async def generate_token(self, password, expire):
        if (expire <= 0):
            raise ValueError('La fecha de expiración debe ser mayor que 0')

        cmd = {
            'cmd'  : 'generate_token',
            'args' : {
                'password' : password,
                'expire'   : expire

            }

        }

        return await self._super_fetch(cmd)

    async def ping(self):
        cmd = {
            'cmd'   : 'ping',
            'token' : self.token

        }

        return await self._super_fetch(cmd)

    async def get_services(self):
        cmd = {
            'cmd'  : 'get_services',
            'token' : self.token

        }

        return await self._super_fetch(cmd)

    async def get_public_key(self):
        cmd = {
            'cmd'   : 'get_public_key',
            'token' : self.token

        }

        return await self._super_fetch(cmd)
