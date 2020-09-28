import ssl

from typing import Tuple, Optional

import aiomysql

from modules.Infrastructure import dbConnector

from utils.General import parse_config

from config import defaults

async def create(
    database: Optional[str] = None,
    only_pool: bool = False,
    config: Optional[dict] = None
    
) -> object:
    """Crear y autoconfigura un conector para MySQL
    
    Args:
        database:
          El nombre de la base de datos.
          Si no se define, se configura según el valor de la clave
          `mysql_db` en el archivo de configuración.

        only_pool:
          Retornar las piscina de conexiones en vez de usar directamente el envoltorio

        config:
          La configuración para el cliente MySQL

    Returns:
        Si `only_pool` es **True** retorna la piscina de conexiones; **False** para
        retornar el envoltorio.
    """

    if (config is None):
        config = parse_config.parse()
    
    db_config = config["MySQL"]
    server_config = config["Server"]

    ssl_context = None
    ssl_key = db_config.get("ssl_key")
    ssl_cert = db_config.get("ssl_cert")
    ssl_ca = db_config.get("ssl_ca")

    if (ssl_key is not None) and (ssl_cert is not None) and (ssl_ca is not None):
        if (server_config["verify_mysql_cert"]):
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=ssl_ca)
            ssl_context.load_cert_chain(
                certfile=ssl_cert, keyfile=ssl_key

            )

        else:
            ssl_context = ssl._create_unverified_context(
                certfile=ssl_cert,
                keyfile=ssl_key,
                cafile=ssl_ca

            )

    if (database is None):
        database = server_config["mysql_db"]

    pool = await aiomysql.create_pool(
        read_default_file=defaults.fileconfig,
        read_default_group="MySQL",
        db=database,
        autocommit=True,
        ssl=ssl_context

    )

    if (only_pool):
        return pool

    else:
        return dbConnector.UTeslaConnector(pool)
