import os
import logging

from utils.General import show_complements

from utils.extra import verify_hash

class Login:
    def __init__(self, 
                 user,
                 userid,
                 init_path='data', 
                 db=None,
                 rsa_object=None):
        self.init_path = init_path
        self.db = db
        self.user = user
        self.userid = userid
        self.rsa_object = rsa_object

        logging.debug('¡(%d) %s se pondrá en interacción con el sistema!', userid, user)

    def ping(self):
        return (200, None)

    async def generate_token(self, password, expire):
        if (expire <= 0):
            return (202, 'Los segundos de expiración deben ser mayor qué 0')

        hash2text = await self.db.get_password(self.userid)

        if (verify_hash.verify(hash2text, password)):
            logging.debug('Generando e insertando token...')

            token = await self.db.insert_token(self.userid, expire)

            return (201, token)

    async def get_services(self):
        complements2show = {}
        complements = show_complements.show(False)
        remote_services = await self.db.get_services()

        for service_name, mtime in remote_services:
            complements2show[service_name] = {
                'mtime' : mtime

            }


        for key, value in complements.items():
            complements2show[key] = {
                'mtime' : value.get('mtime')

            }

        return (200, complements2show)

    async def get_public_key(self):
        return (200, self.rsa_object.export_public_key())
