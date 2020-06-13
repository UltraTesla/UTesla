import urllib.parse

class InvalidURL(Exception):
    """ Cuando la URL es inválida """

def get(network):
    url = urllib.parse.urlsplit(network)

    scheme = url.scheme
    netloc = url.netloc
    # Se verifica que sea un puerto correcto
    url.port

    if not (scheme) or not (netloc):
        raise InvalidURL('¡URL inválida!')

    return '%s://%s' % (scheme, netloc)
