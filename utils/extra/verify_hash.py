import argon2
import logging

def verify(hash2text: str, password: str) -> bool:
    """Verifica si una contraseña es correcta
    
    Args:
        hash2text:
          El hash generado por argon2 sobre la contraseña

        password:
          La contraseña a verificar

    Returns:
        **True** si la contraseña es correcta
    """

    hash_params = argon2.extract_parameters(hash2text)
    hash_func = argon2.PasswordHasher(
        hash_params.time_cost,
        hash_params.memory_cost,
        hash_params.parallelism,
        hash_params.hash_len,
        hash_params.salt_len,
        type=hash_params.type

    )

    return hash_func.verify(hash2text, password)
