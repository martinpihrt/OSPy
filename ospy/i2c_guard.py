# -*- coding: utf-8 -*-

import time
from contextlib import contextmanager
from threading import Lock


_I2C_LOCK = Lock()


@contextmanager
def i2c_transaction(timeout=5.0, settle_time=0.05):
    """Serialize I2C access between plugins running in the OSPy process."""
    start = time.time()
    acquired = False

    while not acquired:
        acquired = _I2C_LOCK.acquire(False)
        if acquired:
            break
        if time.time() - start >= timeout:
            raise IOError('I2C bus is busy.')
        time.sleep(0.05)

    try:
        if settle_time > 0:
            time.sleep(settle_time)
        yield
    finally:
        _I2C_LOCK.release()
