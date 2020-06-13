import msgpack
import concurrent.futures
from secrets import token_bytes

from modules.Crypt import aes_gcm
from modules.Crypt import rsa

# Se coloca el alias 'HASH' para que se modifique con facilidad en
# cada importación de 'hibrid'. Pero éste debe seguir la siguiente
# sintaxis: <HASH MODULE>.new(...)
from Crypto.Hash import SHA3_384 as HASH

from utils.extra import execute_multi_workers

processes = 0

def _rsa(pubKey: rsa.KeyT,
         privKey: rsa.KeyT,
         data: rsa.Message,
         enc: bool = True):
    obj = rsa.Rsa(HASH)

    obj.import_public_key(pubKey)
    obj.import_private_key(privKey)

    if (enc):
        return obj.encrypt_and_sign(pubKey, data)

    else:
        return obj.decrypt_and_verify(pubKey, data)

def _aes(key: aes_gcm.KeyT,
         data: aes_gcm.DataT,
         enc: bool = True) -> bytes:
    obj = aes_gcm.Aes(key)

    if (enc):
        return obj.encrypt(data)

    else:
        return obj.decrypt(data)

def _encrypt(pubKey: rsa.KeyT,
            privKey: rsa.KeyT,
            data: rsa.Message) -> bytes:
    # Agregar un executor usando concurrent.futures
    data = msgpack.dumps(data)
    session_key = token_bytes(aes_gcm.AES.block_size*2)
    enc_key = _rsa(pubKey, privKey, session_key)
    enc_data = _aes(session_key, data)

    return enc_key + enc_data

def _decrypt(privKey: rsa.KeyT,
            pubKey: rsa.KeyT,
            data: rsa.Message) -> bytes:
    key_size = rsa.Rsa().import_public_key(pubKey, False).size_in_bytes() * 2
    enc_key = data[:key_size]
    dec_key = _rsa(pubKey, privKey, enc_key, False)
    enc_data = data[key_size:]

    return msgpack.loads(_aes(dec_key, enc_data, False))

def encrypt(*args, **kwargs):
    return execute_multi_workers.execute(
        _encrypt, processes, *args, **kwargs

    )

def decrypt(*args, **kwargs):
    return execute_multi_workers.execute(
        _decrypt, processes, *args, **kwargs

    )
