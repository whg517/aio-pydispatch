"""
Asyncio pydispatch (Signal Manager)

This is based on [pyDispatcher](http://pydispatcher.sourceforge.net/) reference
[scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html) implementation on
[Asyncio](https://docs.python.org/3/library/asyncio.html)
"""

import asyncio
import functools
import logging
import threading
import weakref
from typing import (Any, Awaitable, Callable, List, Optional, Tuple, TypeVar,
                    Union)

from aio_pydispatch.utils import id_maker, safe_ref

T = TypeVar('T')    # pylint: disable=invalid-name

logger = logging.getLogger(__name__)


class _IgnoredException(Exception):
    """Ignore exception"""


class Signal:
    """
    The signal manager, you can register functions to a signal,
    and store in it.
    Then you can touch off all function that registered on the
    signal where you want.

    example:

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
    """

    def __init__(
            self,
            name: Optional[str] = None,
            doc: Optional[str] = None,
    ):
        self._name = name
        self._doc = doc

        self.__lock = threading.Lock()

        self.__should_clear_receiver = False

        self._receivers = {}

    @property
    def receivers(self):
        """Receivers"""
        return self._receivers

    def connect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
    ) -> Callable[..., Union[T, Awaitable]]:
        """
        Connect a receiver on this signal.
        :param receiver:
        :return:
        """
        assert callable(receiver), "Signal receivers must be callable."

        referenced_receiver = safe_ref(receiver, self._set_should_clear_receiver, value=True)

        lookup_key = id_maker(receiver)

        with self.__lock:
            self._clear_dead_receivers()

            if lookup_key not in self._receivers:
                self._receivers.setdefault(lookup_key, referenced_receiver)
            self._set_should_clear_receiver(False)
        return receiver

    async def send(self, *args, **kwargs) -> List[Tuple[Any, Any]]:
        """Send signal, touch off all registered function."""
        _dont_log = kwargs.pop('_ignored_exception', _IgnoredException)
        responses = []
        loop = asyncio.get_running_loop()
        for receiver in self.live_receivers:
            func = functools.partial(
                receiver,
                *args,
                **kwargs
            )
            try:
                if asyncio.iscoroutinefunction(receiver):
                    response = await func()
                else:
                    response = await loop.run_in_executor(None, func)
            except _dont_log as ex:
                response = ex
            except Exception as ex:  # pylint: disable=broad-except
                response = ex
                logger.error('Caught an error on %s', receiver, exc_info=True)
            responses.append((receiver, response))

        return responses

    def sync_send(self, *args, **kwargs) -> List[Tuple[Any, Any]]:
        """
        Can only trigger sync func. If func is coroutine function,
        it will return a awaitable object.
        :param args:
        :param kwargs:
        :return:
        """
        _dont_log = kwargs.pop('_ignored_exception', _IgnoredException)
        responses = []
        for receiver in self.live_receivers:
            try:
                if asyncio.iscoroutinefunction(receiver):
                    logger.warning('%s is coroutine, but it not awaited', receiver)
                response = receiver(*args, **kwargs)
            except _dont_log as ex:
                response = ex
            except Exception as ex:  # pylint: disable=broad-except
                response = ex
                logger.error('Caught an error on %s', receiver, exc_info=True)
            responses.append((receiver, response))

        return responses

    @property
    def live_receivers(self) -> List[Callable[..., Union[T, Awaitable]]]:
        """Get all live receiver."""
        with self.__lock:
            receivers = []
            _receiver = self._receivers.copy()
            for lookup_key, receiver in _receiver.items():
                if isinstance(receiver, weakref.ReferenceType):
                    real_receiver = receiver()
                    if real_receiver is None:
                        self._receivers.pop(lookup_key)
                    else:
                        receivers.append(real_receiver)
            return receivers

    def _set_should_clear_receiver(self, value: bool) -> None:
        """Register to the receiver weakerf finalize callback"""
        self.__should_clear_receiver = value

    def _clear_dead_receivers(self) -> None:
        if self.__should_clear_receiver:
            _receiver = self._receivers.copy()
            for lookup_key, receiver in _receiver.items():
                if isinstance(receiver, weakref.ReferenceType) and receiver() is not None:
                    continue
                self._receivers.pop(lookup_key)

    def disconnect(self, receiver) -> None:
        """clean a receiver"""
        self._receivers.pop(id_maker(receiver))

    def disconnect_all(self) -> None:
        """Clean all receiver."""
        self._receivers.clear()
