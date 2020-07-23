import asyncio

import pytest


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
