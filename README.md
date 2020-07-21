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
import logging
from aio_pydispatch import SignalManager

logging.basicConfig(level=logging.INFO)

server_start = object()
server_stop = object()

signal_manager = SignalManager()
```

Do something when signal is trigger. Another expression: the signal subscribe the event

```python
def start(data: str) -> None:
    # Do something when server is start.
    logging.info(f'started. {data}')

def stop(data: str) -> None:
    # Do something when server is stop.
    logging.info(f'stoped. {data}')

signal_manager.connect(start, server_start)
signal_manager.connect(start, server_stop)
```

Let's run fake server.

```python

async def run():
    await signal_manager.send(server_start, data=f'xxx')
    await asyncio.sleep(5)
    await signal_manager.send(server_stop, data=f'xxx')


if __name__ == '__main__':
    asyncio.run(run())
```

There is all code:

```python
import asyncio
import logging
from aio_pydispatch import SignalManager

logging.basicConfig(level=logging.INFO)


def start(data: str) -> None:
    logging.info(f'started. {data}')


def stop(data: str) -> None:
    logging.info(f'stopped. {data}')


server_start = object()
server_stop = object()

signal_manager = SignalManager()

signal_manager.connect(start, server_start)
signal_manager.connect(start, server_stop)


async def run():
    await signal_manager.send(server_start, data=f'xxx')
    await asyncio.sleep(5)
    await signal_manager.send(server_stop, data=f'xxx')


if __name__ == '__main__':
    asyncio.run(run())
```

## Similar design

### sync

- [pyDispatcher](http://pydispatcher.sourceforge.net/)
- [Django.dispatch](https://github.com/django/django/tree/master/django/dispatch)
- [scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html)
- [blinker](https://pythonhosted.org/blinker/)

## Others

[Event system in Python](https://stackoverflow.com/a/16192256/11722440)