import configparser

from config import defaults

def parse() -> dict:
    config = configparser.ConfigParser(
        defaults.defaults,
        empty_lines_in_values=False

    )
    config.read(defaults.fileconfig)

    parsed = {}

    dictionary = {
        'Logging'      : [
            ('log_config', str),
            ('critical', str),
            ('error', str),
            ('warning', str),
            ('info', str),
            ('debug', str)

        ],
        
        'Client'       : [
            ('connect_timeout', float),
            ('request_timeout', float),
            ('follow_redirects', bool),
            ('max_redirects', int)

        ],
        
        'Server'       : [
            ('lhost', str),
            ('lport', int),
            ('hash', str),
            ('access_control_allow_origin', str),
            ('mysql_db', str),
            ('max_workers', int),
            ('plugins', str),
            ('user_server', str),
            ('complements', str),
            ('white_list', str),
            ('use_ssl', bool),
            ('ssl_key', str),
            ('ssl_cert', str),
            ('init_path', str),
            ('pub_key', str),
            ('priv_key', str)

        ],
        
        'Proxy'        : [
            ('proxy_type', str),
            ('addr', str),
            ('port', int),
            ('rdns', bool),
            ('username', str),
            ('password', str),
            ('use_proxy', bool)

        ],
        
        'Crypt Limits' : [
            ('time_cost', int),
            ('memory_cost', int),
            ('parallelism', int),
            ('token_length', int),
            ('rsa_key_length', int)

        ],

        'Languages'    : [
            ('language', str),
            ('localedir', str)

        ]

    }

    for section, values in dictionary.items():
        for (value, type) in values:
            if (type == bool):
                convert = config.getboolean

            elif (type == int):
                convert = config.getint

            elif (type == float):
                convert = config.getfloat

            else:
                convert = config.get

            if not (section in parsed):
                parsed[section] = {}

            aux = parsed[section][value] = convert(
                section, value, fallback=defaults.defaults[section][value]

            )

            if (aux in defaults.default_dictionary):
                parsed[section][value] = defaults.default_dictionary[aux]

    return parsed
