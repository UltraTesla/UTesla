import asyncio

from typing import Callable, Optional

from utils.extra import execute_possible_coroutine
from utils.extra import create_translation

_ = create_translation.create("proc_stream")

def is_valid_stream(stream: object, *, exception: bool = False) -> bool:
    """Verifica si una función es válida
    
    Verifica si una función es válida y contiene el método `close`,
    además verifica si es invocable para proceder.

    Args:
        stream:
          Un objeto, estilo `socket.socket()` o `open()`

        exception:
          Si es **True**, en caso de no ser válido el `stream` se llama una excepción

    Returns:
        Si `exception` es **False** se retornará un booleano. Si `stream` es válido se
        retorna **True**, si no, **False**

    Raises:
        TypeError: Si `exception` es **True** y `stream` es inválido
    
    """

    if not (hasattr(stream, "close")) or not (callable(stream.close)):
        if (exception):
            raise TypeError(_("'close' debe estar en el stream y debe poder ser invocado"))

        else:
            return False

    else:
        return True

class ProcStream(dict):
    def __init__(self):
        super().__init__()

        self.__sep = "_"

    def __file_exists(self, name):
        if (super().get(name) is not None):
            return True

        else:
            return False

    def __file_exists_to_err(self, name):
        if not (self.__file_exists(name)):
            raise FileNotFoundError(_("El archivo '{}' no ha sido agregado").format(name))

    def __parse_name(self, name, group=None):
        if (group is not None):
            name = "%s%s%s" % (
                group, self.__sep, name
                    
            )

        return name

    def set_separator(self, sep: str, /) -> None:
        """Ajustar el separador para el grupo y el nombre"""

        self.__sep = sep

    def add_stream(self, stream: object, name: str, *, group: Optional[str] = None) -> None:
        """Agrega un archivo ya abierto

        Args:
            stream:
              Un objeto, estilo `open()` o `socket.socket()`

            name:
              El nombre

            group:
              El nombre del grupo. Se usará el separador.
        """

        is_valid_stream(stream, exception=True)
        name = self.__parse_name(name, group)

        if (self.__file_exists(name)):
            raise FileExistsError(_("El archivo '{}' ya ha sido agregado").format(name))

        super().__setitem__(name, stream)

    __setitem__ = add_stream

    async def async_close(
        self,
        name: str, *,
        group: Optional[str] = None,
        exception: bool = False
        
    ):
        """Cerrar el archivo o flujo"""

        name = self.__parse_name(name, group)

        self.__file_exists_to_err(name)

        stream = super().get(name)

        if not (is_valid_stream(stream, exception=exception)):
            return

        await execute_possible_coroutine.execute(stream.close)

    def close(self, *args, **kwargs):
        """lo mismo que `async_close()` pero sincrónico"""

        return asyncio.run(self.async_close(*args, **kwargs))

    async def async_closeall(self, **kwargs):
        """Cierra todos los archivos"""

        for name in super().keys():
            await self.async_close(name, **kwargs)

    def closeall(self, **kwargs):
        """Lo mismo que `async_closeall()` pero sincrónico"""

        return asyncio.run(self.async_closeall(**kwargs))

    async def async_remove(self, name, **kwargs):
        """Remueve un archivo"""

        await self.async_close(name, **kwargs)
        super().pop(name)

    def remove(self, *args, **kwargs):
        """Lo mismo que `async_remove()` pero sincrónico"""

        return asyncio.run(self.async_remove(*args, **kwargs))

    async def async_removeall(self, **kwargs):
        """Cierra y remueve todos los archivos"""

        for name in super().copy().keys():
            await self.async_remove(name, **kwargs)

    def removeall(self, **kwargs):
        """Lo mismo que `async_removeall()` pero sincrónico"""

        return asyncio.run(self.async_removeall(**kwargs))
