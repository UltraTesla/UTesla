import socks

# Por semántica
default_proxy_types = socks.PROXY_TYPES

# El verdadero diccionario
default_dictionary = {}
default_dictionary.update(default_proxy_types)

# Las claves y valores por defecto en caso de no existir
defaults = {
    "Logging" : {
        "log_config"                   : "config/log_config.json",
        "critical"                     : "{white}[{pink}X{white}]{null}",
        "error"                        : "{white}[{red}-{white}]{null}",
        "warning"                      : "{white}[{yellow}!{white}]{null}",
        "info"                         : "{white}[{blue}*{white}]{null}",
        "debug"                        : "{white}[{green}+{white}]{null}"

    },

    "Templates" : {
        "preface"                      : "Iniciando sesión [%Y-%m-%d %H:%M] para %(address)s:%(port)d",
        "intro"                        : "%(address)s:%(port)d - [%Y-%m-%d %H:%M] %(action)s (%(username)s:%(userid)d)",
        "end"                          : "Sesión finalizada en [%(weeks)d/%(days)d - %(hours)d:%(minutes)d:%(seconds).2f] para %(address)s:%(port)d (%(username)s)",
        "null_data"                    : "null",
        "true_data"                    : "true",
        "false_data"                   : "false"
        
    },

    "Client" : {
        "connect_timewait"             : 30,
        "connect_retry"                : 3,
        "max_buffer_size"              : 2**20*100

    },

    "Server" : {
        "lhost"                        : "127.0.0.1",
        "lport"                        : 17000,
        "mysql_db"                     : "UTesla",
        "plugins"                      : "modules/Cmd",
        "services"                     : "services/",
        "pub_key"                      : "keys/key.pub",
        "priv_key"                     : "keys/key.priv",
        "init_path"                    : "data",
        "user_data"                    : "pubkeys",
        "server_data"                  : "servkeys",
        "init_proc"                    : "processes",
        "clearProcs"                   : .5,
        "memory_limit"                 : 2**20*100,
        "verify_mysql_cert"            : True,
        "recv_timeout"                 : 120,
        "read_chunk_size"              : 2**10*64,
        "index_name"                   : "index",
        "admin_service"                : "admin",
        "autoreload"                   : False,
        "check_time"                   : 500

    },

    "Proxy" : {
        "proxy_type"                   : "SOCKS5",
        "addr"                         : "127.0.0.1",
        "port"                         : 9050,
        "rdns"                         : True,
        "username"                     : None,
        "password"                     : None,
        "use_proxy"                    : False

    },

    "Crypt Limits" : {
        "time_cost"                    : 100,
        "memory_cost"                  : 256000,
        "parallelism"                  : 1000,
        "token_length"                 : 32

    },

    "Languages" : {
        "localedir"                    : "locales",
        "language"                     : "es"

    },

    "MySQL" : {
        "ssl_ca"                       : None,
        "ssl_cert"                     : None,
        "ssl_key"                      : None

    }

}

dictionary = {
    "Logging"      : [
        ("log_config", str),
        ("critical", str),
        ("error", str),
        ("warning", str),
        ("info", str),
        ("debug", str)

    ],

    "Templates" : [
        ("preface", str),
        ("intro", str),
        ("end", str),
        ("null_data", str),
        ("true_data", str),
        ("false_data", str)
        
    ],
    
    "Client"       : [
        ("connect_timewait", int),
        ("connect_retry", int),
        ("max_buffer_size", int)

    ],
    
    "Server"       : [
        ("lhost", str),
        ("lport", int),
        ("mysql_db", str),
        ("plugins", str),
        ("services", str),
        ("init_path", str),
        ("user_data", str),
        ("server_data", str),
        ("pub_key", str),
        ("priv_key", str),
        ("init_proc", str),
        ("clearProcs", float),
        ("memory_limit", int),
        ("verify_mysql_cert", bool),
        ("recv_timeout", int),
        ("read_chunk_size", int),
        ("index_name", str),
        ("admin_service", str),
        ("autoreload", bool),
        ("check_time", int)

    ],
    
    "Proxy"        : [
        ("proxy_type", str),
        ("addr", str),
        ("port", int),
        ("rdns", bool),
        ("username", str),
        ("password", str),
        ("use_proxy", bool)

    ],
    
    "Crypt Limits" : [
        ("time_cost", int),
        ("memory_cost", int),
        ("parallelism", int),
        ("token_length", int)

    ],

    "Languages"    : [
        ("language", str),
        ("localedir", str)

    ],

    # Solo se necesitan extraer dos claves, nada más.
    "MySQL"        : [
        ("ssl_ca", str),
        ("ssl_cert", str),
        ("ssl_key", str)

    ]

}

# El límite de la longitud del nombre de usuario
user_length = 45

# Los archivos de configuración iniciales
sqlfile = "config/database.sql"
fileconfig = "config/UTesla.ini"

# Las extensiones de las carpetas especiales de los servicios y plugins
workspace_extension = "workspace"
config_extension = "config"
shared_dir_extension = "shared"

# Los nombres de los métodos que controlan el comportamiento de los servicios
#
# El nombre del método que indica qué métodos son soportados en el
# servicio que se está analizando actualmente.
supported_methods_name = "SUPPORTED_METHODS"
#
# El nombre del método que indica si el servicio es posible usarlo o no
is_allow_methods_name = "IS_ALLOW"
#
# El nombre del método que indica qué métodos requieren de un token.
# Esto deshabilita la verificación de un token, por lo que si no se usa
# correctamente, puede generar un agujero de seguridad.
is_token_required_methods_name = "NO_TOKEN_REQUIRED"
#
# El nombre del método que se incia antes que cualquier otro método del servicio
# actual.
initializer_methods_name = "INITIALIZER"
#
# El nombre del método que envía un objeto que además de controlar, también contiene
# información de la sesión.
set_controller_methods_name = "SET_CONTROLLER"

# Usado para indicar el final de una transferencia de datos
end_chunk = "\r\n\r\n"

# El nombre de la función de los plugins
mainparser_name = "MainParser"

# El nombre de la clase de los servicios
handler_name = "Handler"

# Los nombres de los métodos del servicio administrativo
access_method = "access"
remote_method = "remote"

# El nombre del diccionario que contiene información del plugin
information_name = "information"
