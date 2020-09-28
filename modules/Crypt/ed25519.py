import inspect
from typing import Tuple, Union, Optional

import nacl.signing

from modules.Crypt import utils
from utils.extra import create_translation
from config import defaults

_ = create_translation.create("ed25519")

def _tuple():
    return utils.key_repr("Ed")

def generate() -> Tuple["nacl.signing.VerifyKey", "nacl.signing.SigningKey"]:
    """Genera el par de claves Ed25519

    Returns:
        Una tupla con la clave de verificación y la clave para firmar
    """

    tuple = _tuple()
    signingKey = nacl.signing.SigningKey.generate()

    return tuple(signingKey.verify_key, signingKey)

def to_raw(
    keys: Tuple["nacl.signing.VerifyKey", "nacl.signing.SigningKey"] = None

) -> Tuple[bytes, bytes]:
    """Convierte un par de claves Ed25519 en un formato válido

    Args:
        keys:
          Las claves generadas por ``generate()``.
          Si no se especifica ninguna, se generan.

    Returns:
        Una tupla con clave de verificación y la clave
        para firmar en bytes.
    
    """

    tuple = _tuple()

    if (keys is None):
        keys = generate()

    return tuple(keys.public._key, keys.private._seed)

def import_keys(
    verifyKey: Optional[bytes] = None,
    signingKey: Optional[bytes] = None
    
) -> Tuple[Optional[bytes], Optional[bytes]]:
    """Importar claves Ed25519

    Args:
        verifyKey:
          La clave de verificación

        signingKey:
          La clave para firmar

    Returns:
        Una tupla con la clave de verificación y la clave
        para firmar.

    Raises:
        TypeError:
          Cuando la clave de verificación o la clave para firmar no son bytes,
          aunque una de las dos o las dos pueden ser opcionales.

    """

    tuple = _tuple()
    keys = {
        "public"  : verifyKey,
        "private" : signingKey
                
    }

    if (verifyKey is not None):
        if not (isinstance(verifyKey, bytes)):
            raise TypeError(_("La clave de verificación no tiene un tipo de dato correcto"))

        keys["public"] = verifyKey

    if (signingKey is not None):
        if not (isinstance(signingKey, bytes)):
            raise TypeError(_("La clave para firmar no tiene un tipo de dato correcto"))

        keys["private"] = signingKey

    return tuple(**keys)

def sign(signingKey: bytes, *args, **kwargs) -> bytes:
    """Firmar datos

    Args:
        signingKey:
          La clave para firmar

        *args:
          Argumentos variables para ``nacl.signing.SigningKey.sign``

        **kwargs:
          Argumentos claves variables para ``nacl.signing.SigningKey.sign``

    Returns:
        El dato firmado
    """

    signing = nacl.signing.SigningKey(signingKey)

    return signing.sign(*args, **kwargs)

def verify(verifyKey: bytes, *args, **kwargs) -> bytes:
    """Verificar los datos firmados

    Args:
        verifyKey:
          La clave para verificar la firma

        *args:
          Argumentos variables para ``nacl.signing.VerifyKey.verify``

        **kwargs:
          Argumentos claves variables para ``nacl.signing.VerifyKey.verify``

    Returns:
        El mismo dato que se introdujo al firmar
    
    """

    verifySignature = nacl.signing.VerifyKey(verifyKey)

    return verifySignature.verify(*args, **kwargs)
