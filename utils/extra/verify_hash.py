import argon2
import logging

def verify(hash2text, password):
    hash_params = argon2.extract_parameters(hash2text)
    hash_func = argon2.PasswordHasher(
        hash_params.time_cost,
        hash_params.memory_cost,
        hash_params.parallelism,
        hash_params.hash_len,
        hash_params.salt_len,
        type=hash_params.type

    )

    logging.debug('Verificando la validez de la contraseña...')

    return hash_func.verify(hash2text, password)
