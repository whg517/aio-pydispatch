import asyncio
import functools
import logging
import threading
import weakref
from typing import Awaitable, Callable, List, Optional, TypeVar, Union

from aio_pydispatch.utils import make_id, safe_ref

T = TypeVar('T')

logger = logging.getLogger(__name__)


class _IgnoredException(Exception):
    """Ignore exception"""


class Signal:

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

    def connect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
    ):
        """
        Connect a receiver on this signal
        :param receiver:
        :return:
        """
        assert callable(receiver), "Signal receivers must be callable."

        receiver = safe_ref(receiver, self._set_should_clear_receiver, value=True)

        lookup_key = make_id(receiver)

        with self.__lock:
            self._clear_dead_receivers()

            if lookup_key not in self._receivers:
                self._receivers.setdefault(lookup_key, receiver)
            self._set_should_clear_receiver(False)

    async def send(self, *args, **kwargs):
        _dont_log = kwargs.pop('_dont_log', _IgnoredException)
        responses = []
        loop = asyncio.get_running_loop()
        for receiver in self._live_receivers():
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
            except _dont_log as e:
                response = e
            except Exception as e:
                response = e
                logger.error(f'Caught an error on {receiver}', exc_info=True)
            responses.append((receiver, response))

        return responses

    def _live_receivers(self) -> List[Callable[..., Union[T, Awaitable]]]:
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
        self.__should_clear_receiver = value

    def _clear_dead_receivers(self):
        if self.__should_clear_receiver:
            _receiver = self._receivers.copy()
            for lookup_key, receiver in _receiver.items():
                if isinstance(receiver, weakref.ReferenceType) and receiver() is not None:
                    continue
                self._receivers.pop(lookup_key)

    def disconnect(self, receiver):
        self._receivers.pop(make_id(receiver))

    def disconnect_all(self):
        self._receivers.clear()
