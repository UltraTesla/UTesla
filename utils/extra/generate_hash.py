import argon2

def generate(password, time_cost, memory_cost,
             parallelism, crypt_limits, *args,
             **kwargs):
    for origin, limit in [(time_cost, crypt_limits.get('time_cost')),
                          (memory_cost, crypt_limits.get('memory_cost')),
                          (parallelism, crypt_limits.get('parallelism'))]:
        if (origin > (limit + 1)):
            raise exceptions.LimitsExceeded('Los límites pre-configurados no permiten seguir con la operación')

    argon_func = argon2.PasswordHasher(
        time_cost, memory_cost, parallelism,
        32, *args, type=argon2.Type.ID, **kwargs

    )

    return argon_func.hash(password)
