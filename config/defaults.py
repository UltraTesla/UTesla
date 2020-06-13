import socks

import Crypto.Hash.SHA3_384
import Crypto.Hash.MD5
import Crypto.Hash.MD4
import Crypto.Hash.SHA1
import Crypto.Hash.SHA224
import Crypto.Hash.SHA256
import Crypto.Hash.SHA512

# Por semántica
default_hash = {
    'SHA3_384' : Crypto.Hash.SHA3_384,
    'MD5'      : Crypto.Hash.MD5,
    'MD4'      : Crypto.Hash.MD4,
    'SHA1'     : Crypto.Hash.SHA1,
    'SHA224'   : Crypto.Hash.SHA224,
    'SHA256'   : Crypto.Hash.SHA256,
    'SHA512'   : Crypto.Hash.SHA512

}

default_proxy_types = socks.PROXY_TYPES

# El verdadero diccionario
default_dictionary = {}
default_dictionary.update(default_hash)
default_dictionary.update(default_proxy_types)

# Las claves y valores por defecto en caso de no existir
defaults = {
    'Logging' : {
        'log_config'                   : 'config/log_config.json',
        'critical'                     : '{white}[{pink}X{white}]{null}',
        'error'                        : '{white}[{red}-{white}]{null}',
        'warning'                      : '{white}[{yellow}!{white}]{null}',
        'info'                         : '{white}[{blue}*{white}]{null}',
        'debug'                        : '{white}[{green}+{white}]{null}'

    },

    'Client'  : {
        'connect_timeout'              : 30.0,
        'request_timeout'              : 30.0,
        'follow_redirects'             : True,
        'max_redirects'                : 5,
        'user_agent'                   : 'Ultra Tesla - Client 1.0',
        'use_gzip'                     : False

    },

    'Server'  : {
        'lhost'                        : '127.0.0.1',
        'lport'                        : 17000,
        'hash'                         : 'SHA3_384',
        'access_control_allow_origin'  : '*',
        'mysql_db'                     : 'UTesla',
        'max_workers'                  : 0,
        'plugins'                      : 'modules/Cmd',
        'user_server'                  : 'utesla',
        'complements'                  : 'complements/',
        'white_list'                   : '.*',
        'use_ssl'                      : False,
        'ssl_key'                      : None,
        'ssl_cert'                     : None,
        'pub_key'                      : 'keys/key.pub',
        'priv_key'                     : 'keys/key.priv',
        'init_path'                    : 'data'

    },

    'Proxy' : {
        'proxy_type'                   : 'SOCKS5',
        'addr'                         : '127.0.0.1',
        'port'                         : 9050,
        'rdns'                         : True,
        'username'                     : None,
        'password'                     : None,
        'use_proxy'                    : False

    },

    'Crypt Limits' : {
        'time_cost'                    : 100,
        'memory_cost'                  : 256000,
        'parallelism'                  : 1000,
        'token_length'                 : 32,
        'rsa_key_length'               : 3072

    },

    'Languages'    : {
        'localedir'                    : 'locales',
        'language'                     : 'es'

    }

}

# Los nombres de archivos vitales y nombres de las extensiones
sqlfile = 'config/database.sql'
fileconfig = 'config/UTesla.ini'
sub_services_extension = 'folder'
modules_extension = 'modules'
workspace_extension = 'workspace'
# Los comandos que no requieren token
no_token_required = [
    'generate_token',
    'get_services'

]
# Usado por get_argument y get_arguments
write_methods = [
    'PUT',
    'POST',
    'PATCH',
    'DELETE'

]
# Los tipos de datos aceptados para opciones futuras
content_types = [
    'application/octet-stream'

]
# El que usa el servidor por defecto
default_type = content_types[0]
