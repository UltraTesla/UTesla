class UnknownOption(Exception):
    """ Cuando una opción es desconocida """

class UserNotExists(Exception):
    """ Cuando el usuario no existe """

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

class EmptyReply(Exception):
    """ Cuando la respuesta está vacia """

class NetworkNotExists(Exception):
    """ Cuando la red no existe """
