from typing import Any

import pytest
from pydispatch import dispatcher
from pydispatch.dispatcher import getReceivers

from aio_pydispatch.signal import Signal


class TestSignal:

    @pytest.fixture()
    def signal(self):
        signal = Signal()
        yield signal
        signal.disconnect_all()

    def test_connect(self, signal, start, async_start):
        signal.connect(start)
        assert len(getReceivers(signal.__class__, signal)) == 1
        signal.connect(async_start)
        assert len(getReceivers(signal.__class__, signal)) == 2
        signal.disconnect_all()
        assert len(getReceivers(signal.__class__, signal)) == 0
