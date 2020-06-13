import concurrent.futures
import multiprocessing

def execute(func, max_workers=0,
            *args, **kwargs):
    if (max_workers == 0):
        max_workers = multiprocessing.cpu_count()

    with concurrent.futures.ProcessPoolExecutor(max_workers) as executor:
        task = executor.submit(func, *args, **kwargs)
        
    return task.result()
