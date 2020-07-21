import asyncio

import pytest
from pydispatch import dispatcher

from aio_pydispatch.signal_manager import SignalManager

start_signal = object()


def start(x):
    return x


async def async_start(x):
    await asyncio.sleep(0)
    return x


class TestSignalManager:

    @pytest.fixture()
    def signal_manager(self):
        sm = SignalManager(self)
        yield sm
        sm.disconnect_all(start_signal)

    @pytest.fixture()
    def signal_manager_connected_async(self, signal_manager):
        signal_manager.connect(async_start, start_signal)
        yield signal_manager
        signal_manager.disconnect_all(start_signal)

    @pytest.fixture()
    def signal_manager_connected_sync(self, signal_manager):
        signal_manager.connect(start, start_signal)
        yield signal_manager
        signal_manager.disconnect_all(start_signal)

    def test_connect(self, signal_manager):
        signal_manager.connect(start, start_signal)
        assert len(dispatcher.connections) == 1

    def test_disconnect(self, signal_manager):
        assert len(dispatcher.connections) == 0

        signal_manager.connect(start, start_signal)
        assert len(dispatcher.connections) == 1

        signal_manager.disconnect(async_start, start_signal)
        assert len(dispatcher.connections) == 1

        signal_manager.disconnect(start, start_signal)
        assert len(dispatcher.connections) == 0

    def test_disconnect_all(self, signal_manager):
        assert len(dispatcher.connections) == 0

        signal_manager.connect(start, start_signal)
        assert len(dispatcher.connections) == 1

        signal_manager.disconnect_all(start_signal)
        assert len(dispatcher.connections) == 0

    @pytest.mark.asyncio
    async def test_send_async(self, signal_manager_connected_async):
        res = await signal_manager_connected_async.send(start_signal, x='foo')
        assert (async_start, 'foo') in res

    @pytest.mark.asyncio
    async def test_send_sync(self, signal_manager_connected_sync):
        res = await signal_manager_connected_sync.send(start_signal, x='foo')
        assert (start, 'foo') in res

    @pytest.mark.asyncio
    async def test_send_async_exception(self, signal_manager, caplog):
        e = ValueError('xxx')

        async def demo(x):
            raise e

        signal_manager.connect(demo, start_signal)

        res = await signal_manager.send(start_signal, x='foo')
        assert (demo, e) in res
        assert 'Caught an error on signal handler: ' in caplog.text

    @pytest.mark.asyncio
    async def test_send_async_exception_dont_log(self, signal_manager, caplog):
        e = ValueError('xxx')

        async def demo(x):
            raise e

        signal_manager.connect(demo, start_signal)

        res = await signal_manager.send(start_signal, x='foo', dont_log=ValueError)
        assert (demo, e) in res
        assert 'Caught an error on signal handler: ' not in caplog.text
