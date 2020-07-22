from typing import Callable, Awaitable, Union, TypeVar, Any

from aio_pydispatch import SignalManager

T = TypeVar('T')


class Signal:

    def __init__(self, name: str = 'Anonymous'):
        self._signal_manager = SignalManager(self.__class__)
        self._name = name

    def connect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
            **kwargs,
    ):
        """
        :param receiver:
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        self._signal_manager.connect(receiver, self, **kwargs)

    def connect_via(self, **kwargs):
        """
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """

        def _decorator(func: Callable[..., Union[T, Awaitable]]):
            self.connect(func, **kwargs)

            return func

        return _decorator

    async def send(self, **kwargs: Any):
        """
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        await self._signal_manager.send(self, **kwargs)

    def disconnect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
            **kwargs,
    ):
        """
        :param receiver:
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        self._signal_manager.disconnect(receiver, self, **kwargs)

    def disconnect_all(self, **kwargs):
        """
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        self._signal_manager.disconnect_all(self, **kwargs)
