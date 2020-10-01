import inspect
from typing import Optional, Tuple

import nacl.public

from modules.Crypt import utils

def _tuple():
    return utils.key_repr("Curve")

def generate(
    sk: "nacl.public.PrivateKey" = None

) -> Tuple["nacl.public.PublicKey", "nacl.public.PrivateKey"]:
    """Genera un par de claves Curve25519

    Args:
        sk:
          La clave privada
    
    Returns:
        Una tupla con la clave pública y la clave privada
    """

    tuple = _tuple()

    if (sk is None):
        sk = nacl.public.PrivateKey.generate()

    return tuple(sk.public_key, sk)

def to_raw(
    keys: Tuple["nacl.public.PublicKey", "nacl.public.PrivateKey"] = None
    
) -> Tuple[bytes, bytes]:
    """Convierte un par de claves Curve25519 en un formato válido
    
    Args:
        keys:
          Las claves generadas por ``generate()``.
          Si no se especifica ninguna, se generan.

    Returns:
        Una tupla con la clave pública y la clave privada en bytes
    """

    tuple = _tuple()

    if (keys is None):
        keys = generate()

    return tuple(keys.public._public_key, keys.private._private_key)

class InitSession(object):
    """Crea una sesión para el intercambio de claves

    Inicia una sesión para intercambiar claves entre dos partes
    y a su vez, entablar una comunicación segura.
    """

    def __init__(
        self,
        pk_dst: bytes,
        sk_src: Optional[bytes] = None
        
    ):
        """Crea y/o importa tanto las claves del destinatario como del remitente
        
        Args:
            pk_dst:
              La clave pública del destinatario

            sk_src:
              La clave privada del remitente.
              Si no se especifica, se genera.
        """

        if (sk_src is None):
            self._sk_src = nacl.public.PrivateKey.generate()

        else:
            self._sk_src = nacl.public.PrivateKey(sk_src)
        
        self._pk_dst = nacl.public.PublicKey(pk_dst)

        self._box = nacl.public.Box(self._sk_src, self._pk_dst)

    @property
    def destination(self) -> bytes:
        """La clave pública del destinatario"""

        return self._pk_dst._public_key

    @property
    def source(self) -> bytes:
        """La clave pública y privada del remitente"""

        return to_raw(generate(self._sk_src))

    def encrypt(self, *args, **kwargs) -> bytes:
        """Encripta datos"""

        return self._box.encrypt(*args, **kwargs)

    def decrypt(self, *args, **kwargs) -> bytes:
        """Descifra datos"""

        return self._box.decrypt(*args, **kwargs)
