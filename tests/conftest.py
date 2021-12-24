"""Tests."""
import asyncio

import pytest

from aio_pydispatch.signal import Signal


@pytest.fixture()
def error_kls():
    """Error fixture."""
    yield ValueError


@pytest.fixture()
def start_error(error_kls):
    """Start error fixture."""

    def _(name: str, **kwargs):
        raise error_kls(name, kwargs)

    return _


@pytest.fixture()
def async_start_error(error_kls):
    """Async start error fixture."""

    async def _(name: str, **kwargs):
        raise error_kls(name, kwargs)

    return _


@pytest.fixture()
def start():
    """Start fixture."""

    def _(name: str, **kwargs):
        return name, kwargs

    return _


@pytest.fixture()
def async_start():
    """Async start fixture."""

    async def _(name, **kwargs):
        await asyncio.sleep(0)
        return name, kwargs

    return _


@pytest.fixture()
def signal():
    """Signal fixture."""
    _signal = Signal()
    yield _signal
    _signal.disconnect_all()
