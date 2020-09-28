# Permite usar constantes para mayor legibilidad y con el 
# objetivo de describir en un solo código de estado el error
# en particular.

from errno import *

from utils.extra import create_translation

_ = create_translation.create("errno")

ENOTOK = 1000
ENOACT = 1001
ETOKEXPIRED = 1002
ESERVER = 1003
ENOUSR = 1004
ECLIENT = 1005
ETOKLIMIT = 1006
ENOSRV = 1007

default_messages = {
    ENOTOK      : _("El token es requerido para la autenticación"),
    ENOACT      : _("No se ha definido la acción o no está habilitada"),
    ETOKEXPIRED : _("El token ha expirado"),
    ESERVER     : _("Error interno en el servidor"),
    ENOUSR      : _("El usuario no existe"),
    ECLIENT     : _("Petición inválida"),
    ETOKLIMIT   : _("Límites de tokens alcanzados"),
    ENOSRV      : _("El servicio no está habilitado"),
    EPERM       : _("Permiso denegado")

}

for key, value in [
                (ENOTOK, "ENOTOK"),
                (ENOACT, "ENOACT"),
                (ETOKEXPIRED, "ETOKEXPIRED"),
                (ESERVER, "ESERVER"),
                (ENOUSR, "ENOUSR"),
                (ECLIENT, "ECLIENT"),
                (ETOKLIMIT, "ETOKLIMIT"),
                (ENOSRV, "ENOSRV")

            ]:
    errorcode[key] = value
