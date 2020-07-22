import asyncio
import functools
import logging
from typing import Awaitable, Callable, List, TypeVar, Union, Any

from pydispatch import dispatcher, robustapply
from pydispatch.dispatcher import getAllReceivers, liveReceivers

T = TypeVar('T')

logger = logging.getLogger(__name__)


class SignalManager:

    def __init__(self, sender=dispatcher.Anonymous):
        self._sender = sender

    def connect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
            signal: Any,
            *,
            weak: bool = True,
            **kwargs: Any
    ) -> None:
        """
        Connect a event to a signal.
        when send this signal, this event will be trigger.
        :param receiver:
        :param signal:
        :param weak:
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        kwargs.setdefault('sender', self._sender)
        dispatcher.connect(receiver, signal, weak=weak, **kwargs)

    def connect_via(
            self,
            signal: Any,
            *,
            weak: bool = True,
            **kwargs: Any
    ):
        """
        Decorate func to connect a signal.
        :param signal:
        :param weak:
        :param kwargs:
            sender Any, default dispatcher.Any
        :return:
        """

        def _decorator(func: Callable[..., Union[T, Awaitable]]):
            self.connect(func, signal, weak=weak, **kwargs)

            return func

        return _decorator

    async def send(self, signal: Any, **kwargs: Any) -> List:
        """
        Sends a signal to trigger the event to which it is connected.
        :param signal:
        :param kwargs:
            sender: Any, default dispatcher.Any
            dont_log: Optional[Exception]
            ...     other kwargs will pass func.
        :return:
        """
        kwargs.setdefault('sender', self._sender)
        return await send(signal, **kwargs)

    def disconnect(
            self,
            receiver: Callable[..., Union[T, Awaitable]],
            signal: Any,
            **kwargs: Any
    ) -> None:
        """
        Disconnect event and signal
        :param receiver:
        :param signal:
        :param kwargs:
        :return:
        """
        kwargs.setdefault('sender', self._sender)
        dispatcher.disconnect(receiver, signal, **kwargs)

    def disconnect_all(self, signal: Any, **kwargs: Any) -> None:
        """
        Disconnect all event from signal.
        :param signal:
        :param kwargs:
            sender: Any, default dispatcher.Any
        :return:
        """
        kwargs.setdefault('sender', self._sender)
        disconnect_all(signal, **kwargs)


class _IgnoredException(Exception):
    pass


def disconnect_all(signal=dispatcher.Any, sender=dispatcher.Any) -> None:
    for receiver in list(liveReceivers(getAllReceivers(sender, signal))):
        dispatcher.disconnect(receiver, signal=signal, sender=sender)


async def send(signal: Any, sender: Any, *args: Any, **kwargs: Any) -> List:
    """
    触发订阅该信号的事件。
    如果订阅该信号的事件是同步方法，会使用 event_loop.run_in_executor 方法运行。暂时仅
    支持默认的 executor 即:concurrent.futures.ThreadPoolExecutor。

    注意：执行所有事件的时候如果出现异常不会触发 raise 而是捕获异常放到返回值中，如果你需要
    根据异常做出对应操作，你应该从返回值中判断，而非在执行事件的过程中直接 raise
    :param signal:
    :param sender:
    :param args:
    :param kwargs:
        dont_log: bool 可以通过设置期待异常，在出现异常的时候不会触发 error 日志。
    :return:
    """
    responses: List = []
    dont_log = kwargs.pop('dont_log', _IgnoredException)
    for receiver in liveReceivers(getAllReceivers(sender, signal)):
        func = functools.partial(
            robustapply.robustApply,
            receiver=receiver,
            signal=signal,
            sender=sender,
            *args,
            **kwargs
        )
        try:
            if not asyncio.iscoroutinefunction(receiver):
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, func)
            else:
                response = await func()
        except dont_log as e:
            response = e
        except Exception as e:
            response = e
            logger.error(f"Caught an error on signal handler: {receiver}", exc_info=True)

        responses.append((receiver, response))
    return responses
