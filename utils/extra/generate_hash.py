import argon2
from typing import Optional

from modules.Infrastructure import exceptions

from utils.extra import create_translation

_ = create_translation.create("generate_hash")

def generate(
    password: str,
    time_cost: int,
    memory_cost: int,
    parallelism: int,
    crypt_limits: Optional[dict] = None,
    *args, **kwargs
    
) -> str:
    """Hash a `password` y retorna el hash codificado.
    
    Args:
        password:
          La contraseña en texto plano

        time_cost:
          La cantidad de calculo utilizado

        memory_cost:
          Define el uso de memoria en KiB

        parallelism:
          Define el número de subprocesos paralelos

        hash_len:
          La longitud del hash

        salt_len:
          Longitud de la «salt» aleatoria que se generará para cada contraseña

        crypt_limits:
          La configuración para limitar el uso de parámetros excesivos

        *args:
          Argumentos variables para `argon2.PasswordHasher()`

        **kwargs:
          Argumentos claves variables para `argon2.PasswordHasher()`

    Returns:
        El hash de la contraseña

    Raises:
        exceptions.LimitsExceeded:
          Cuando los límites pre-configurados no permiten
          seguir con la operación.
    """

    if (crypt_limits is not None):
        options = (
            (time_cost, crypt_limits["time_cost"]),
            (memory_cost, crypt_limits["memory_cost"]),
            (parallelism, crypt_limits["parallelism"])
                
        )

        for origin, limit in options:
            if (origin > limit):
                raise exceptions.LimitsExceeded(
                    _("Los límites pre-configurados no permiten seguir con la operación")

                )

    argon_func = argon2.PasswordHasher(
        time_cost, memory_cost, parallelism,
        32, *args, type=argon2.Type.ID, **kwargs

    )

    return argon_func.hash(password)
