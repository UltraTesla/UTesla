import MySQLdb
import logging

from config import defaults

from modules.Infrastructure import dbConnector

def init(db, sqlfile):
    logging.debug('Conectando a MySQL de forma sincrónica...')

    db_object = MySQLdb.connect(read_default_file=defaults.fileconfig,
                                read_default_group='MySQL', autocommit=True)
    cursor = db_object.cursor()
    
    logging.debug('Creando base de datos: %s', db)

    cursor.execute('CREATE DATABASE IF NOT EXISTS %s' % (db))

    logging.debug('Leyendo archivo SQL inicial: %s', sqlfile)

    with open(sqlfile, 'r') as sqlfile_fd:
        result = sqlfile_fd.read()

        for sqlscript in result.split(';'):
            sqlscript = sqlscript.strip()
            
            if (sqlscript):
                cursor.execute(sqlscript)

    logging.debug('Cerrando conexión con MySQL...')

    cursor.close()
    db_object.close()
