import aiomysql

from modules.Infrastructure import dbConnector

from utils.General import parse_config

from config import defaults

async def create(database=None):
    if (database is None):
        database = parse_config.parse()['Server']['mysql_db']

    pool = await aiomysql.create_pool(
        read_default_file=defaults.fileconfig,
        read_default_group='MySQL',
        db=database,
        autocommit=True

    )

    return dbConnector.UTeslaConnector(pool)
