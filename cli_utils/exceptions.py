class InformationNotFoundError(Exception):
    """ Cuando no existe el diccionario de información del plugin """

class MainFunctionNotFoundError(Exception):
    """ Cuando la función principal de un plugin no existe """

class ArgumentsError(Exception):
    """ La función no debería más de un argumento y no debería recibir argumentos clave """
