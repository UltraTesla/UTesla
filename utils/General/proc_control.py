import asyncio
import threading
import multiprocessing
import sys
import copy

from typing import Callable, Optional, Union, Any

from utils.extra import create_translation

_ = create_translation.create("proc_control")

class invalidTarget(Exception):
    " Si el objetivo deseado no se encuentra "

class ThreadSafe(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self) 

    def __run(self):
        sys.settrace(self.global_trace)
        self.__run_backup()
        self.run = self.__run_backup 

    def global_trace(self, frame, event, arg):
        if (event == "call"):
            return self.local_trace

        else:
            return None

    def local_trace(self, frame, event, arg):
        if self.killed:
            if event == "line":
                raise SystemExit()

        return self.local_trace 

    def kill(self):
        self.killed = True

class ProcControl(dict):
    def __init__(self, procName: str, interval: float = .5):
        """
        Args:
            procName:
              El nombre del objetivo.
              'threads' para crear, usar y administrar subprocesos.
              `processes` para crear, usar y administrar procesos
              en paralelo.

            interval:
              El tiempo de espera antes de remover (ya sean subprocesos o procesos)
              y después de mandar una señal SIGTERM/SIGKILL.
        """

        super().__init__()

        self.__procName = procName
        self.interval = interval

        self._check_error()

        super().__setitem__("threads", {})
        super().__setitem__("processes", {})

    def _check_error(self):
        if (self.__procName != "threads") and (self.__procName != "processes"):
            raise invalidTarget(_("El objetivo no es válido"))
    
    def _get_target_name(self, target=None):
        if (target is None):
            target = self.__procName

        return target

    def _get_target(self, target=None):
        target = self._get_target_name(target)

        if (target == "threads"):
            return ThreadSafe

        else:
            return multiprocessing.Process

    def getTarget(self) -> str:
        """Obtener el nombre actual del objetivo"""

        return self.__procName

    def getInterval(self) -> float:
        """Obtener el intervalo actual"""

        return self.interval

    def setTarget(self, procName: str) -> None:
        """Ajustar el objetivo"""

        _backup = self.__procName

        self.__procName = procName

        try:
            self._check_error()

        except:
            self.__procName = _backup

            raise

    def create(
        self,
        function: Callable[..., Any],
        start: bool = True,
        *args,
        target: Optional[str] = None,
        **kwargs
        
    ) -> str:
        """Crea un nuevo procedimiento

        Dependiendo del objetivo usado, creará un proceso en paralelo o subproceso.

        Args:
            function:
              Debe ser una función y debe poder ser invocada

            start:
              Al terminar de agregarla, **True** para invocarla, **False** si no.

            *args:
              Los argumentos variables usado por el objetivo.
              Los cuales pueden ser `TheadSafe` o `multiprocessing.Process`
              dependiendo de cómo esté configurado.

            target:
              Decide si ejecutarlo como un proceso o un subproceso.
              Esta opción inválida la opción global definida por
              `setTarget()` y no lo modifica.

            **kwargs:
              Los argumentos claves variables usados por el objetivo.

        Returns:
          El nombre del subproceso o proceso.

        Raises:
            ValueError: Cuando ya existe un nombre del subproceso o proceso.
            TypeError: La función o el objeto a llamar no puede ser invocado
        """

        if not (callable(function)):
            raise TypeError(_("La función no puede ser llamada"))

        target = self._get_target_name(target)

        targetObj = self._get_target(target)(
            *args, target=function, **kwargs

        )

        procs = super().__getitem__(target)
        
        if (targetObj.name in procs):
            raise ValueError(_("%s ya existe") % (targetObj.name))

        if (start):
            targetObj.start()

        procs[targetObj.name] = targetObj

        return targetObj.name

    def _remove(self, procName, key):
        proc = super().__getitem__(procName)[key]

        if not (proc.is_alive()):
            super().__getitem__(procName).pop(key)

    def autoRemove(self, item: Optional[str] = None) -> None:
        """Remueve los procesos/subprocesos finalizados pero no eliminados
        
        Args:
            item:
              El nombre del proceso/subproceso
        """

        for procName in super().keys():
            if (item is None):
                items = copy.copy(super().__getitem__(procName))

                for key in items.keys():
                    self._remove(procName, key)

            else:
                self._remove(procName, item)

    def stop(self, item: Union["multiprocessing.context", "ThreadSafe"], killProc: bool = False) -> None:
        """Parar el proceso/subproceso en ejecución

        Args:
            item:
              Un objeto `multiprocessing.context` o `ThreadSafe`

            killProc:
              **True** manda una señal SIGKILL; **False** una SIGTERM
        """

        if (item.__module__ == "multiprocessing.context"):
            if (killProc):
                item.kill()

            else:
                item.terminate()

        else:
            item.kill()
            item.join()

    def autoStop(self, *args, **kwargs) -> None:
        """Ejecuta `stop()` para cada item agregado"""

        for items in super().values():
            for item in items.values():
                self.stop(item, *args, **kwargs)

    def clear(self, *args, **kwargs) -> None:
        """Los mismo que `AsyncClear()` pero sincrónico"""

        asyncio.run(self.AsyncClear(*args, **kwargs))

    async def AsyncClear(self, *args, **kwargs) -> None:
        """Ejecuta `autoStop()` y `autoRemove()` juntos"""

        for target in super().keys():
            self.autoStop(*args, **kwargs)
            # Esperamos que terminen los procesos, aunque pueden no terminar :-p
            await asyncio.sleep(self.interval)
            self.autoRemove()

    def __len__(self):
        return len(super().__getitem__(self.__procName))

    def __iter__(self):
        return iter(super().__getitem__(self.__procName))

    def __getitem__(self, item):
        return super().__getitem__(self.__procName)[item]

    def getProc(self, item, target=None):
        """Obtener el proceso/subproceso"""

        target = self._get_target_name(target)

        return super().__getitem__(target)[item]

    get = __getitem__
