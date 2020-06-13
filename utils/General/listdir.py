import os

from typing import (Optional,
                    Callable)

def list(callback: Callable,
         path: str = '.',
         recursive: bool = True,
         only_dirs: bool = False,
         *args, **kwargs):
    try:
        files = os.listdir(path)
    
    except Exception as Except:
        callback(path, True, Except,
                 *args, **kwargs)

        return

    for file in files:
        file = '%s/%s' % (path, file)

        if (os.path.isdir(file)):
            callback(file, True, None,
                     *args, **kwargs)

            if (recursive):
                list(
                    callback,
                    file,
                    recursive,
                    only_dirs,
                    *args, **kwargs

                )

        else:
            if not (only_dirs):
                callback(file, False, None,
                         *args, **kwargs)
