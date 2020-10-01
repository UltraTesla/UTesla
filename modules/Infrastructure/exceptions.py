class LimitsExceeded(Exception):
    """ Cuando los limites pre-configurados son excedidos """

class TokenLimitsExceeded(Exception):
    """ Cuando los límites de los tokens por usuario son excedidos """

class NonExistentToken(Exception):
    """ Cuando el token no existe """

class PublicKeyNotFound(Exception):
    """ Cuando la clave pública no existe """

class InvalidRequest(Exception):
    """ Cuando la petición es inválida """

class RootHandlerNotExists(Exception):
    """ Cuando el archivo controlador no se encuentra """

class UserNotFound(Exception):
    """ Cuando el usuario/ID no existe """
