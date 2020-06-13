from Crypto.Cipher import AES
from secrets import token_bytes

from typing import Union

DataT = Union[bytes,
              bytearray,
              memoryview]

KeyT = DataT

class Aes(object):
    def __init__(self, password: KeyT):
        self.password = password

    def encrypt(self, data: DataT) -> bytes:
        """
        Cifra los datos.

        :param data:
            Los datos a cifrar.
        :type data: bytes/bytearray/memoryview

        :Return: Los datos cifrados.
        """

        nonce = token_bytes(AES.block_size)
        cipher = AES.new(self.password,
                         AES.MODE_GCM,
                         nonce)

        (ciphertext, tag) = cipher.encrypt_and_digest(data)

        return nonce + tag + ciphertext

    def decrypt(self, data: DataT) -> bytes:
        """
        Descifra los datos.

        :param data:
            Los datos a descifrar.
        :type data: bytes/bytearray/memoryview

        :Return: Los datos descifrados.
        """

        nonce = data[:AES.block_size]
        tag = data[AES.block_size:AES.block_size*2]
        ciphertext = data[AES.block_size*2:]

        cipher = AES.new(self.password,
                         AES.MODE_GCM,
                         nonce)

        return cipher.decrypt_and_verify(ciphertext, tag)
