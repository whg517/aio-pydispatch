import asyncio

import pytest


@pytest.fixture()
def error():
    yield ValueError('foo')


@pytest.fixture()
def start_error(error):
    def _(x):
        raise error

    return _


@pytest.fixture()
def async_start_error(error):
    async def _(x):
        raise error

    return _


@pytest.fixture()
def start():
    def _(x):
        return x

    return _


@pytest.fixture()
def async_start():
    async def _(x):
        await asyncio.sleep(0)
        return x

    return _
