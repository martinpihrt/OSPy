# -*- coding: utf-8 -*-

import time
from contextlib import contextmanager
from threading import Condition


_I2C_CONDITION = Condition()
_I2C_ACTIVE = False
_I2C_PRIORITIES = {
    'high': 0,
    'normal': 1,
    'low': 2,
}
_I2C_WAITING = [0, 0, 0]


@contextmanager
def i2c_transaction(timeout=30.0, settle_time=0.02, priority='normal'):
    """Serialize I2C access between plugins running in the OSPy process."""
    global _I2C_ACTIVE

    priority_level = _I2C_PRIORITIES.get(priority, _I2C_PRIORITIES['normal'])
    deadline = time.time() + timeout

    with _I2C_CONDITION:
        _I2C_WAITING[priority_level] += 1
        try:
            while True:
                higher_priority_waiting = any(_I2C_WAITING[level] > 0 for level in range(priority_level))
                if not _I2C_ACTIVE and not higher_priority_waiting:
                    _I2C_ACTIVE = True
                    break

                remaining = deadline - time.time()
                if remaining <= 0:
                    raise IOError('I2C bus is busy.')
                _I2C_CONDITION.wait(min(0.05, remaining))
        finally:
            _I2C_WAITING[priority_level] -= 1

    try:
        yield
    finally:
        if settle_time > 0:
            time.sleep(settle_time)
        with _I2C_CONDITION:
            _I2C_ACTIVE = False
            _I2C_CONDITION.notify_all()
