# aio_pydispatch

![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/whg517/aio-pydispatch/main/main?style=flat-square)
![GitHub](https://img.shields.io/github/license/whg517/aio-pydispatch?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/aio_pydispatch?style=flat-square)
[![codecov](https://codecov.io/gh/whg517/aio-pydispatch/branch/main/graph/badge.svg?token=YF339UJGAD)](https://codecov.io/gh/whg517/aio-pydispatch)

Asyncio pydispatch (Signal Manager)

This is based on [pyDispatcher](http://pydispatcher.sourceforge.net/) reference
[Django Signals](https://docs.djangoproject.com/en/4.0/topics/signals/) and reference
[scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html) implementation on
[Asyncio](https://docs.python.org/3/library/asyncio.html)

## Event or Signal (not python bif signal)

You can bind multiple listeners (called sender) to listening multiple handlers (called receiver)
on one event (called signal). 

Default, the listener is None, so when the event is fire with no listener, all handlers will be 
executed that was bind default listener.

## Usage

Most of the program has `start` and `stop` events, we can register some handler to events,
we can also specify a sender.

```python
import asyncio

from aio_pydispatch import Signal

server_start = Signal()
server_stop = Signal()


def ppp(value: str, **kwargs) -> None:
    print(value, kwargs)


async def main():
    server_start.connect(ppp, sender='loading config')
    server_stop.connect(ppp)
    await server_start.send(sender='loading config', value='foo')
    await asyncio.sleep(1)
    await server_stop.send(value='foo')


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