"""
Asyncio pydispatch (Signal Manager)

This is based on [pyDispatcher](http://pydispatcher.sourceforge.net/) reference
[Django Signals](https://docs.djangoproject.com/en/4.0/topics/signals/) and reference
[scrapy SignalManager](https://docs.scrapy.org/en/latest/topics/signals.html) implementation on
[Asyncio](https://docs.python.org/3/library/asyncio.html)
"""

import asyncio
import functools
import logging
import threading
import weakref
from collections.abc import Awaitable
from typing import Any, Callable, TypeVar, Union

from aio_pydispatch.utils import func_accepts_kwargs, id_maker, safe_ref

T = TypeVar('T')  # pylint: disable=invalid-name
Receiver = Callable[..., Union[T, Awaitable]]

logger = logging.getLogger(__name__)


class _IgnoredException(Exception):
    """
    Ignore exception.
    """


class Signal:
    """
    Signal, or event.

    example:
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

    """

    def __init__(self):
        """Signal, or event."""
        self.__lock = threading.Lock()
        self.__clean_receiver = False

        self._all_receivers: dict[int, dict[int, Any]] = {}

    @property
    def receivers(self):
        """Receivers."""
        return self._all_receivers

    def connect(
            self,
            receiver: Receiver,
            sender: Any = None,
            weak=True,
    ):
        """
        Connect a receiver on this signal.

        :param receiver:
        :param sender:
        :param weak:
        :return:
        """
        assert callable(receiver), "Signal receivers must be callable."

        if not func_accepts_kwargs(receiver):
            raise ValueError("Signal receivers must accept keyword arguments (**kwargs).")

        sender_key = id_maker(sender)
        receiver_key = id_maker(receiver)
        if weak:
            receiver = safe_ref(receiver, self._enable_clean_receiver)

        with self.__lock:
            self._clean_dead_receivers()
            receivers = self._all_receivers.get(sender_key, {})
            receivers.setdefault(receiver_key, receiver)
            self._all_receivers.update({sender_key: receivers})

    async def send(self, *, sender: Any = None, **kwargs) -> list[tuple[Any, Any]]:
        """Send signal, touch off all registered function."""
        _dont_log = kwargs.pop('_ignored_exception', _IgnoredException)
        responses = []
        loop = asyncio.get_running_loop()
        for receiver in self.live_receivers(sender):
            func = functools.partial(
                receiver,
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

    def sync_send(self, *, sender: None = None, **kwargs) -> list[tuple[Any, Any]]:
        """
        Can only trigger sync func. If func is coroutine function,
        it will return awaitable object
        :param sender:
        :param kwargs:
        :return:
        """
        _dont_log = kwargs.pop('_ignored_exception', _IgnoredException)
        responses = []
        for receiver in self.live_receivers(sender):
            try:
                if asyncio.iscoroutinefunction(receiver):
                    logger.warning('%s is coroutine, but it not awaited', receiver)
                response = receiver(**kwargs)
            except _dont_log as ex:
                response = ex
            except Exception as ex:  # pylint: disable=broad-except
                response = ex
                logger.error('Caught an error on %s', receiver, exc_info=True)
            responses.append((receiver, response))
        return responses

    def live_receivers(self, sender: None = None) -> list[Receiver]:
        """Get all live receiver."""
        with self.__lock:
            self._clean_dead_receivers()
            receivers: dict[int, Any] = self._all_receivers.get(id_maker(sender), {})
            real_receivers = []
            has_dead = False
            for receiver_key, receiver in receivers.copy().items():
                if isinstance(receiver, weakref.ReferenceType):
                    real_receiver: Callable = receiver()
                    if real_receiver:
                        real_receivers.append(real_receiver)
                    else:
                        # receiver is dead
                        has_dead = True
                        receivers.pop(receiver_key)
                else:
                    # not use weak for receiver
                    real_receivers.append(receiver)
            # update cleaned sender of receiver to all receivers
            if has_dead:
                self._all_receivers.update({id_maker(sender): receivers})
            return real_receivers

    def _enable_clean_receiver(self) -> None:
        """Register to the receiver weakerf finalize callback."""
        self.__clean_receiver = True

    def _clean_dead_receivers(self) -> None:
        if self.__clean_receiver:
            self.__clean_receiver = False
            for receivers in self._all_receivers.values():
                for receiver_key, receiver in receivers.copy().items():
                    if isinstance(receiver, weakref.ReferenceType) and receiver() is None:
                        receivers.pop(receiver_key)

    def disconnect(self, receiver: Receiver, sender: Any = None) -> None:
        """Clean receivers of a sender."""
        lookup_key = id_maker(sender)
        receiver_key = id_maker(receiver)
        with self.__lock:
            receivers: dict[int, Any] = self._all_receivers.get(lookup_key)
            receiver_ref = receivers.pop(receiver_key)
            if receivers and receiver_ref:
                self._all_receivers.update({lookup_key: receivers})

    def disconnect_all(self) -> None:
        """Clean all receiver."""
        self._all_receivers.clear()


def connect(signal: Signal, sender: Any = None, weak=True):
    """
    Connect decorator.

    :param signal:
    :param sender:
    :param weak:
    :return:
    """

    def _decorator(func):
        if isinstance(signal, Signal):
            signal.connect(receiver=func, sender=sender, weak=weak)
        return func

    return _decorator
