# aio_pydispatch

Asyncio pydispatch (Signal Manager)

This is based on [pyDispatcher](http://pydispatcher.sourceforge.net/) reference
[scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html) implementation on
[Asyncio](https://docs.python.org/3/library/asyncio.html)


## Usage

Like the situation often encountered on the web

Init some signals and a signal manager

```python
import asyncio

from aio_pydispatch import Signal

server_start = Signal('server_start')
server_stop = Signal('server_stop')


def ppp(value: str) -> None:
    print(value)


async def main():
    server_start.connect(ppp)
    server_stop.connect(ppp)
    await server_start.send('server start')
    await asyncio.sleep(1)
    await server_stop.send('server stop')


if __name__ == '__main__':
    asyncio.run(main())
```

## Similar design

### sync

- [pyDispatcher](http://pydispatcher.sourceforge.net/)
- [Django.dispatch](https://github.com/django/django/tree/master/django/dispatch)
- [scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html)
- [blinker](https://pythonhosted.org/blinker/)

### async

- [Aiohttp tracing](https://github.com/aio-libs/aiohttp/blob/master/aiohttp/tracing.py)

## Others

[Event system in Python](https://stackoverflow.com/a/16192256/11722440)