import threading
import multiprocessing
import sys
import copy
import time

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
        if (event == 'call'):
            return self.local_trace

        else:
            return None

    def local_trace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()

        return self.local_trace 

    def kill(self):
        self.killed = True

class ProcControl(dict):
    def __init__(self, procName, interval=.5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__procName = procName
        self.interval = interval

        self._check_error()

        super().__setitem__('threads', {})
        super().__setitem__('processes', {})

    def _check_error(self):
        if (self.__procName != 'threads') and (self.__procName != 'processes'):
            raise invalidTarget('El objetivo no es válido')
    
    def _get_target(self):
        if (self.__procName == 'threads'):
            return ThreadSafe

        else:
            return multiprocessing.Process

    def setTarget(self, procName):
        _backup = self.__procName

        self.__procName = procName

        try:
            self._check_error()

        except:
            self.__procName = _backup

            raise

    def create(self, target, start=True, *args, **kwargs):
        targetObj = self._get_target()(
            *args, target=target, **kwargs

        )

        procs = super().__getitem__(self.__procName)
        
        if (targetObj.name in procs):
            raise ValueError('%s ya existe' % (targetObj.name))

        if (start):
            targetObj.start()

        procs[targetObj.name] = targetObj

        return targetObj.name

    def _remove(self, procName, key):
        proc = super().__getitem__(procName)[key]

        if not (proc.is_alive()):
            super().__getitem__(procName).pop(key)

    def autoRemove(self, item=None):
        for procName in super().keys():
            if (item is None):
                items = copy.copy(super().__getitem__(procName))

                for key in items.keys():
                    self._remove(procName, key)

            else:
                self._remove(procName, item)

    def stop(self, item, killProc=False):
        if (item.__module__ == 'multiprocessing.context'):
            if (killProc):
                item.kill()

            else:
                item.terminate()

        else:
            item.kill()
            item.join()

    def autoStop(self, *args, **kwargs):
        for items in super().values():
            for item in items.values():
                self.stop(item, *args, **kwargs)

    def clear(self, *args, **kwargs):
        _backup = self.__procName

        for target in super().keys():
            self.setTarget(target)
            self.autoStop(*args, **kwargs)
            # Esperamos que terminen los procesos, aunque pueden no terminar :-p
            time.sleep(self.interval)
            self.autoRemove()

        # Se restaura el objetivo original
        self.setTarget(_backup)
    
    def __len__(self):
        return len(super().__getitem__(self.__procName))

    def __iter__(self):
        return iter(super().__getitem__(self.__procName))

    def __getitem__(self, item):
        return super().__getitem__(self.__procName)[item]

    get = __getitem__
