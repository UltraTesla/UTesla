import asyncio

async def execute(function, *args, **kwargs):
    if (asyncio.iscoroutinefunction(function)):
        val = await function(*args, **kwargs)

    else:
        val = function(*args, **kwargs)

    return val
