"""Tests"""
import asyncio

import pytest

from aio_pydispatch.signal import Signal


@pytest.fixture(name='error')
def fixture_error():
    """Error fixture"""
    yield ValueError('foo')


@pytest.fixture()
def start_error(error):
    """start error fixture"""

    def _(_name: str):
        raise error

    return _


@pytest.fixture()
def async_start_error(error):
    """async start error fixture"""

    async def _(_name: str):
        raise error

    return _


@pytest.fixture()
def start():
    """start fixture"""

    def _(name: str):
        return name

    return _


@pytest.fixture()
def async_start():
    """async start fixture"""

    async def _(name):
        await asyncio.sleep(0)
        return name

    return _


@pytest.fixture()
def signal():
    """Signal fixture"""
    _signal = Signal()
    yield _signal
    _signal.disconnect_all()
