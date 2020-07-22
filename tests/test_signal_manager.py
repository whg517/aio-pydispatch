import asyncio

import pytest
from pydispatch import dispatcher
from pydispatch.dispatcher import getAllReceivers, getReceivers

from aio_pydispatch.signal_manager import SignalManager


class TestSignalManager:

    @pytest.fixture()
    def signal(self):
        yield object()

    @pytest.fixture()
    def signal_manager(self, signal):
        sm = SignalManager(self)
        yield sm
        sm.disconnect_all(signal)

    def test_disconnect(self, signal_manager, signal, start, async_start):
        assert len(getReceivers(self, signal)) == 0

        signal_manager.connect(start, signal)
        assert len(getReceivers(self, signal)) == 1

        signal_manager.connect(async_start, signal)
        assert len(getReceivers(self, signal)) == 2

        signal_manager.disconnect(async_start, signal)
        assert len(getReceivers(self, signal)) == 1

        signal_manager.disconnect(start, signal)
        assert len(getReceivers(self, signal)) == 0

    def test_disconnect_all(self, signal_manager, signal, start, async_start):
        signal_manager.connect(start, signal)
        signal_manager.connect(async_start, signal)

        assert len(getReceivers(self, signal)) == 2

        signal_manager.disconnect_all(signal)
        assert len(getReceivers(self, signal)) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ('mode_async',),
        [
            (True,),
            (True,),
        ]
    )
    async def test_send(self, signal_manager, signal, start, async_start, mode_async):
        func = async_start if mode_async else start
        signal_manager.connect(func, signal)
        res = await signal_manager.send(signal, x='foo')
        assert (func, 'foo') in res

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ('dont_log',),
        [
            (True,),
            (False,)
        ]
    )
    async def test_send_catch_log(self, signal_manager, signal, dont_log, caplog):
        e = ValueError('xxx')

        async def demo(x):
            raise e

        signal_manager.connect(demo, signal)

        kwargs = {
            'x': 'foo'
        }

        if dont_log is False:
            kwargs.update({'dont_log': e.__class__})

        res = await signal_manager.send(signal, **kwargs)
        assert (demo, e) in res
        assert ('Caught an error on signal handler: ' in caplog.text) == dont_log
