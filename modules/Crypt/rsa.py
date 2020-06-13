from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pss
from Crypto.Hash import SHA3_384 as Hash

# Control de excepciones
try:
    import exceptions

except ModuleNotFoundError:
    # Cuando se use el paquete en sí
    from modules.Crypt import exceptions

# Semántica
from typing import (Union,
                    Tuple,
                    Any,
                    Optional,
                    Callable,
                    NoReturn)

# La claves RSAs
RsaKey = object

# El tipo de la llamada para interactuar con los datos
Interact = object

# El mensaje a encriptar/desencriptar
Message = Union[str,
                bytes,
                bytearray,
                memoryview]

KeyT = Union[str, bytes]

class Rsa(object):
    def __init__(self, hash_func=Hash):
        self.privateKey: RsaKey = None
        self.publicKey: RsaKey  = None

        self.pubInteract: Interact = None
        self.privInteract: Interact = None

        self.hash_func = Hash

    def __generate_interacts(self):
        """ Genera los objetos para encriptar/desencriptar datos """

        if (self.privateKey):
            self.privInteract = PKCS1_OAEP.new(self.privateKey)

        if (self.publicKey):
            self.pubInteract = PKCS1_OAEP.new(self.publicKey)

    def generate(self, bits: int = 3072) -> Tuple[RsaKey, RsaKey]:
        """
        Genera el par de claves

        :param bits:
            El tamaño en bits del par de claves.

            El valor predeterminado (3072) es considerado excelente
            en la actualidad, pero podría cambiar en un futuro.
        :type bits: int

        :Return: Una tupla con los objetos del par de claves: (Clave Privada,
        Clave Pública)
        """

        self.privateKey = RSA.generate(bits)
        self.publicKey = self.privateKey.publickey()

        self.__generate_interacts()

        return (self.privateKey,
                self.publicKey)

    def export_keys(self, all: dict = dict(pkcs=8),
                          pub_args: Optional[dict] = None,
                          priv_args: Optional[dict] = None) -> Tuple[bytes, bytes]:
        """
        Exporta el par de claves.

        Nota: El método 'export_keys' usa internamente los métodos
              'export_private_key' y 'export_public_key'.

        :param all:
            Los argumentos usados tanto en el método 'export_private_key'
            y 'export_public_key'.
        :type all: dict

        :param pub_args:
            Los argumentos usados en el parámetro 'export_public_key'.
        :type pub_args: dict

        :param priv_args:
            Los argumentos usados en el parámetro 'export_private_key'.
        :type priv_args: dict

        :Return: Una tupla con el par de claves: (Clave Privada, Clave Pública)
        """

        return (self.export_private_key(**all, **pub_args),
                self.export_public_key(**all, **priv_args))


    def export_private_key(self, *args: Any, **kwargs: Any) -> bytes:
        """ Exporta la clave privada. """

        return self.privateKey.export_key(*args,
                                          **kwargs)

    def export_public_key(self, *args: Any, **kwargs: Any) -> bytes:
        """ Exporta la clave pública. """

        return self.publicKey.export_key(*args,
                                         **kwargs)

    @staticmethod
    def __strtobytes(data: str) -> Union[str, Any]:
        """ Convierte un string (str) en bytes (bytes). """

        return data.encode() if (isinstance(data, str)) else data

    def encrypt(self, pubKey: KeyT,
                      data: Message) -> bytes:
        """
        Cifra los datos.

        :param pubKey:
            La clave pública del receptor.
        :type pubKey: str/bytes

        :param data:
            Los datos a cifrar.
        :type data: str/bytes/bytearray/memoryview

        :Return: El mensaje cifrado en 'bytes'
        """

        data = self.__strtobytes(data)
        pubInteract = PKCS1_OAEP.new(self.import_public_key(pubKey,
                                                            False))

        return pubInteract.encrypt(data)

    def decrypt(self, data: Message) -> bytes:
        """
        Descifra los datos.

        :param data:
            Los datos a descifrar.
        :type data: str/bytes/bytearray/memoryview

        :Return: El mensaje descifrado en 'bytes'
        """

        data = self.__strtobytes(data)

        return self.privInteract.decrypt(data)

    @staticmethod
    def __check_key(key: KeyT,
                    priv: bool) -> Union[NoReturn, bytes]:
        """ Verifica que una clave sea privada o pública """

        priv = not priv
        
        if (key.has_private() == priv):
            raise exceptions.invalid_key('La clave pública de entrada no es válida')

        else:
            return key

    def import_public_key(self, pubKey: KeyT,
                                overwrite: bool = True,
                                passphrase: Optional = None) -> Union[NoReturn, RsaKey]:
        """
        Importa la clave pública.

        :param pubKey:
            La clave pública.
        :type pubKey: str/bytes

        :param overwrite:
            Si es 'True' se sobreescribe la propiedad 'publicKey' por
            el valor de 'pubKey'.

            Si es 'False' se retorna un objeto RSA con la clave pública
            para interactuar con éste.
        :type overwrite: bool

        :param passphrase:
            La frase de contraseña para desencriptarla en la importación.
        :type passphrase: str/bytes

        :Return:
            Si 'overwrite' es 'True' retorna 'None', si es 'False'
            retorna un objeto RSA.
        """

        key = self.__check_key(
            RSA.import_key(pubKey, passphrase), False

        )

        if (overwrite):
            self.publicKey = key
            self.__generate_interacts()

        else:
            return key

    def import_private_key(self, privKey: KeyT,
                                 overwrite: bool = True,
                                 passphrase: Optional = None) -> Union[NoReturn, bytes]:
        """
        Importa la clave privada.

        :param privKey:
            La clave privada.
        :type privKey: str/bytes

        :param overwrite:
            Si es 'True' se sobreescribe la propiedad 'privateKey' por
            el valor de 'privKey'.

            Si es 'False' se retorna un objeto RSA con la clave privada
            para interactuar con éste.
        :type overwrite: bool

        :param passphrase:
            La frase de contraseña para desencriptarla en la importación.
        :type passphrase: str/bytes

        :Return:
            Si 'overwrite' es 'True' retorna 'None', si es 'False'
            retorna un objeto RSA.
        """

        key = self.__check_key(
            RSA.import_key(privKey, passphrase), True

        )

        if (overwrite):
            self.privateKey = key
            self.__generate_interacts()

        else:
            return key

    def sign(self, msg_hash: Callable) -> bytes:
        """
        Firmar un mensaje usando RSA.

        :param msg_hash:
            La instancia del módulo para la firma.

            Por ejemplo:
                sign(SHA3_256.new(b'test'))
        :type msg_hash: Callable

        :Return: El mensaje firmado
        """

        _pss = pss.new(self.privateKey)
        
        return _pss.sign(msg_hash)

    def verify(self, pubKey: KeyT,
                     signature: bytes,
                     msg_hash: Callable) -> NoReturn:
        """
        Verificar un mensaje firmado.

        :param pubKey:
            La clave pública para la verificación del mensaje
            firmado.
        :type pubKey: str/bytes

        :param signature:
            El mensaje firmado.
        :type signature: bytes

        :param msg_hash:
            La instancia de un nuevo objeto '<Hash>.new(b'<datos>')'.

            Nota: Debe incluir el mensaje en 'new' para compararlo
                  con la firma.
        :type msg_hash: Callable

        :Return: No retorna nada si no se generó un error.
        """

        _publicKey = self.import_public_key(pubKey, False)

        _pss = pss.new(_publicKey)

        _pss.verify(msg_hash, signature)

    def encrypt_and_sign(self, pubKey: KeyT,
                               data: Message,
                               hash_callback: Callable = None) -> bytes:
        """
        Cifra y firma los datos a la misma vez.

        :param pubKey:
            La clave pública.
        :type pubKey: str/bytes

        :param data:
            Los datos a cifrar y firmar.
        :type data: str/bytes/bytearray/memoryview

        :param hash_callback:
            La instancia de un nuevo objeto '<Hash>.new(b'<datos>')'.

            Nota: No se debe incluir un mensaje en 'new', éste se
            usará internamente en 'verify'.
            
        :type hash_callback: Callable

        :Return: El mensaje cifrado y firmado en 'bytes'
        """

        if not (hash_callback):
            hash_callback = self.hash_func.new()

        enc_data = self.encrypt(pubKey, data)
        hash_callback.update(enc_data)
        signed = self.sign(hash_callback)

        return signed + enc_data

    def decrypt_and_verify(self, pubKey: KeyT,
                                 data: Message,
                                 msg_hash: Callable = None) -> bytes:
        """
        Descifrar y verificar los datos a la misma vez.

        :param pubKey:
            La clave pública.
        :type pubKey: str/bytes

        :param data:
            Los datos a descifrar y verificar.
        :type data: str/bytes/bytearray/memoryview

        :param msg_hash:
            La instancia de un nuevo objeto '<Hash>.new(b'<datos>')'.

            Nota: No debe incluir un mensaje en 'new', éste se
            usará internamente en 'verify'.
            
        :type msg_hash: Callable

        :Return: El mensaje descifrado y verificado en 'bytes'
        """

        if not (msg_hash):
            msg_hash = self.hash_func.new()

        key = self.import_public_key(pubKey, False)
        signed = data[:key.size_in_bytes()]
        enc_data = data[key.size_in_bytes():]
        msg_hash.update(enc_data)
        self.verify(pubKey, signed, msg_hash)

        return self.decrypt(enc_data)
