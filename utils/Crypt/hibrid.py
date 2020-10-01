import msgpack

from modules.Crypt import x25519_xsalsa20_poly1305MAC
from modules.Crypt import ed25519
from utils.Crypt import options

def encrypt(
    signingKey: bytes,
    publicKey: bytes,
    secretKey: bytes,
    data: bytes,
    is_packed: bool = options.IS_PACKED

) -> bytes:
    """Cifra y firma un mensaje
    
    Args:
        signingKey:
          La clave para firmar

        publicKey:
          La clave pública del destinatario

        secretKey:
          La clave secreta

        data:
          Los datos a cifrar

        is_packed:
          Usar o no `msgpack`

    Returns:
        Los datos cifrados y firmados
    """

    scheme = x25519_xsalsa20_poly1305MAC.InitSession(publicKey, secretKey)

    return ed25519.sign(signingKey, scheme.encrypt(
        data if not (is_packed) else msgpack.dumps(data)
        
    ))

def decrypt(
    verifyKey: bytes,
    publicKey: bytes,
    secretKey: bytes,
    data: bytes,
    is_packed: bool = options.IS_PACKED

) -> bytes:
    """Descifra y verifica el mensaje

    Args:
        verifyKey:
            La clave de verificación

        publickey:
            La clave pública del destinatario

        secretKey:
            La clave secreta

        data:
            Los datos a descifrar

    Returns:
        Los datos verificados y descifrados
    """

    scheme = x25519_xsalsa20_poly1305MAC.InitSession(publicKey, secretKey)
    
    result = scheme.decrypt(ed25519.verify(verifyKey, data))

    if (is_packed):
        return msgpack.loads(result)

    else:
        return result
