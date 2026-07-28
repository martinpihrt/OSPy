"""Replayable in-process event stream for native API clients."""

import collections
import datetime
import json
import threading
import time


MAX_EVENTS = 1000


class EventStream(object):
    def __init__(self):
        self._condition = threading.Condition()
        self._events = collections.deque(maxlen=MAX_EVENTS)
        self._next_id = 1

    def publish(self, event_type, data=None):
        with self._condition:
            event = {
                "id": self._next_id,
                "event": str(event_type),
                "data": data or {},
                "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self._next_id += 1
            self._events.append(event)
            self._condition.notify_all()
            return dict(event)

    def after(self, event_id, limit=200):
        event_id = int(event_id or 0)
        limit = max(1, min(int(limit or 200), 500))
        with self._condition:
            return [
                dict(item) for item in self._events
                if item["id"] > event_id
            ][:limit]

    def wait_after(self, event_id, timeout=15):
        deadline = time.time() + max(0, timeout)
        with self._condition:
            while not any(item["id"] > event_id for item in self._events):
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)
            return [
                dict(item) for item in self._events if item["id"] > event_id
            ]

    @staticmethod
    def encode_sse(event):
        return "id: {id}\nevent: {event}\ndata: {data}\n\n".format(
            id=event["id"],
            event=event["event"],
            data=json.dumps(event["data"], separators=(",", ":"), ensure_ascii=False),
        )


event_stream = EventStream()
