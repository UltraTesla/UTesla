import os
import hashlib
import logging
import aiofiles
import tornado.escape

from modules.Infrastructure import exceptions

from utils.Crypt import hibrid

class Parser:
    def __init__(self, init_path=None, rsa_object=None):
        self.init_path = init_path
        self.rsa = rsa_object

    @staticmethod
    def __check_pubkey(pubkey_path):
        if not (os.path.isfile(pubkey_path)):
            raise exceptions.PublicKeyNotFound('Error, la clave pública "%s" no existe' % (
                pubkey_path)

            )

    @staticmethod
    def __real_user_generator(user):
        return hashlib.sha3_224(
            user.encode()

        ).digest()

    def build(self, user, message, dest_key):
        real_user = self.__real_user_generator(user)

        logging.debug('Cifrando datos con el usuario "%s"...' % (user))
        
        return real_user + hibrid.encrypt(
            dest_key,
            self.rsa.export_private_key(),
            message

        )

    async def reply(self, user, message):
        real_user = self.__real_user_generator(user)

        pubkey_path = '%s/pubkeys/%s' % (
            self.init_path, real_user.hex()

        )

        logging.debug('Usando clave pública (%s) del usuario "%s" para responder...', 
            pubkey_path, user

        )

        self.__check_pubkey(pubkey_path)

        async with aiofiles.open(pubkey_path, 'rb') as pubkey_fd:
            logging.debug('Cifrando la respuesta para el usuario "%s"', user)

            public_key = await pubkey_fd.read()

            return hibrid.encrypt(
                public_key,
                self.rsa.export_private_key(),
                message

            )

    def get_message(self, pubkey, data):
        return hibrid.decrypt(
            self.rsa.export_private_key(),
            pubkey,
            data

        )

    async def destroy(self, data):
        real_user = tornado.escape.url_escape(
            data[:28].hex()

        )
        message = data[28:]
        pubkey_path = '%s/pubkeys/%s' % (
            self.init_path, real_user

        )

        if (len(real_user) != 28*2) or (len(message) <= 0):
            raise exceptions.InvalidRequest('¡Petición inválida!')

        self.__check_pubkey(pubkey_path)

        async with aiofiles.open(pubkey_path, 'rb') as pubkey_fd:
            logging.debug('Descifrando datos del identificador "%s"...', real_user)

            public_key = await pubkey_fd.read()

            return (
                real_user, hibrid.decrypt(
                self.rsa.export_private_key(),
                public_key,
                message)

            )
