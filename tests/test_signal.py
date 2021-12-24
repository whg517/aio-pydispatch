"""Test signal"""
import inspect

import pytest

from aio_pydispatch.signal import connect


class Foo:
    """Mock class"""

    def start(self, **kwargs):
        """foo start"""


def test_connect(signal, start, async_start):
    """Test connect"""
    assert len(signal.receivers) == 0

    foo1 = Foo()
    foo2 = Foo()
    signal.connect(foo1.start)
    signal.connect(foo2.start)
    assert len(signal.live_receivers()) == 2
    del foo1

    signal.connect(start)

    signal.connect(async_start)

    del foo2
    assert len(signal.live_receivers()) == 2

    signal.disconnect(start)
    assert len(signal.live_receivers()) == 1
    signal.disconnect_all()
    assert len(signal.live_receivers()) == 0


def test_connect_error(signal):
    """Test signal connect a no kwargs receiver"""
    def _(_a, *_args):
        """foo"""

    with pytest.raises(ValueError):
        signal.connect(_)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('mode_async',),
    [
        (True,),
        (False,),
    ]
)
async def test_send(signal, start, async_start, mode_async):
    """Test send"""
    func = async_start if mode_async else start
    signal.connect(func)
    responses = await signal.send(name=1)
    assert (func, (1, {})) in responses


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('_ignored_exception', 'mode_async'),
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]
)
async def test_send_error(
        signal,
        start_error,
        async_start_error,
        error_kls,
        _ignored_exception,
        mode_async,
        caplog
):
    """Test send error"""
    func = async_start_error if mode_async else start_error
    signal.connect(func)

    if _ignored_exception:
        await signal.send(name='foo', _ignored_exception=error_kls)
        assert f'Caught an error on {func}' not in caplog.text
    else:
        await signal.send(name='foo')
        assert f'Caught an error on {func}' in caplog.text


@pytest.mark.filterwarnings('ignore')
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mode_async',
    [True, False]
)
def test_sync_send(signal, start, async_start, mode_async, caplog):
    """Test sync send"""
    func = async_start if mode_async else start
    signal.connect(func)
    responses = signal.sync_send(name=1)
    for receiver, response in responses:
        if not mode_async:
            assert response == (1, {})
            assert 'but it not awaited' not in caplog.text
        if receiver == async_start:
            assert inspect.isawaitable(response)
            assert f'{receiver} is coroutine, but it not awaited' in caplog.text


@pytest.mark.filterwarnings('ignore')
@pytest.mark.parametrize(
    ('_ignored_exception', 'mode_async'),
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]
)
def test_sync_send_error(
        signal,
        start_error,
        async_start_error,
        error_kls,
        _ignored_exception,
        mode_async,
        caplog
):
    """Test sync send error"""
    func = async_start_error if mode_async else start_error
    signal.connect(func)
    if _ignored_exception:
        signal.sync_send(name='foo', _ignored_exception=error_kls)
        assert f'Caught an error on {func}' not in caplog.text
    else:
        signal.sync_send(name='foo')
        if mode_async:
            assert f'{func} is coroutine, but it not awaited' in caplog.text
        else:
            assert f'Caught an error on {func}' in caplog.text


def test_connect_decorator(signal):
    """Test connect decorator"""
    @connect(signal)
    def _(**_kwargs):
        """fpp"""

    assert len(signal.receivers) == 1
