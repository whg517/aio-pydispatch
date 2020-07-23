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
        ('_dont_log',),
        [
            (True,),
            (False,),
        ]
    )
    async def test_send_error(self, signal, _dont_log, caplog):
        e = ValueError('foo')

        def foo():
            raise e

        kwargs = {}
        if _dont_log:
            kwargs.update({'_dont_log': e.__class__})

        signal.connect(foo)
        await signal.send(**kwargs)
        assert not (f'Caught an error on {foo}' in caplog.text) == _dont_log
