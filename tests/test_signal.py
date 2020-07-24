import inspect

import pytest

from aio_pydispatch.signal import Signal


class Foo:

    def start(self): ...


class TestSignal:

    @pytest.fixture()
    def signal(self):
        signal = Signal()
        yield signal
        signal.disconnect_all()

    def test_connect(self, signal, start, async_start):
        assert len(signal._receivers) == 0

        foo1 = Foo()
        foo2 = Foo()
        signal.connect(foo1.start)
        signal.connect(foo2.start)
        assert len(signal._live_receivers()) == 2
        del foo1

        signal.connect(start)

        signal.connect(async_start)

        del foo2
        assert len(signal._live_receivers()) == 2

        signal.disconnect(start)
        assert len(signal._live_receivers()) == 1
        signal.disconnect_all()
        assert len(signal._live_receivers()) == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ('mode_async',),
        [
            (True,),
            (False,),
        ]
    )
    async def test_send(self, signal, start, async_start, mode_async):
        func = async_start if mode_async else start
        signal.connect(func)
        responses = await signal.send(x=1)
        assert (func, 1) in responses

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ('_dont_log', 'mode_async'),
        [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]
    )
    async def test_send_error(self, signal, start_error, async_start_error, error, _dont_log, mode_async, caplog):
        func = async_start_error if mode_async else start_error
        kwargs = {'x': 1}
        if _dont_log:
            kwargs.update({'_dont_log': error.__class__})

        signal.connect(func)
        await signal.send(**kwargs)
        assert not (f'Caught an error on {func}' in caplog.text) == _dont_log

    @pytest.mark.filterwarnings('ignore')
    def test_sync_send(self, signal, start, async_start, caplog):
        signal.connect(start)
        signal.connect(async_start)
        responses = signal.sync_send(x=1)
        for receiver, response in responses:
            if receiver == start:
                assert response == 1
            if receiver == async_start:
                assert inspect.isawaitable(response)
                assert f'{receiver} is coroutine, but it not awaited' in caplog.text

    @pytest.mark.filterwarnings('ignore')
    @pytest.mark.parametrize(
        ('_dont_log', 'mode_async'),
        [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]
    )
    def test_sync_send_error(self, signal, start_error, async_start_error, error, _dont_log, mode_async, caplog):
        func = async_start_error if mode_async else start_error
        kwargs = {'x': 1}
        if _dont_log:
            kwargs.update({'_dont_log': error.__class__})

        signal.connect(func)
        signal.sync_send(**kwargs)
        if mode_async:
            assert not (f'Caught an error on {func}' in caplog.text)
        else:
            assert not (f'Caught an error on {func}' in caplog.text) == _dont_log
