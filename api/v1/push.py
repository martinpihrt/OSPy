"""Asynchronous, installation-scoped push relay client."""

import hashlib
import hmac
import json
import queue
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from ospy.log import log

from .store import mobile_store


QUEUE_LIMIT = 256
REQUEST_TIMEOUT = 10


def notification_category(event_type, code):
    if code == "station_started":
        return "station_started"
    if code == "station_stopped":
        return "station_stopped"
    if event_type == "rain" or str(code).startswith("rain_"):
        return "rain"
    if event_type == "diagnostics":
        return "diagnostics"
    if event_type == "updates" or str(code).startswith("update_"):
        return "updates"
    if event_type == "automation" or str(code).startswith("automation_rule_"):
        return "automation"
    return "other"


def validate_relay_url(value):
    value = str(value or "").strip().rstrip("/")
    if not value:
        return ""
    parsed = urlparse(value)
    loopback = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    try:
        parsed_port = parsed.port
    except ValueError:
        raise ValueError("The push relay URL is not valid.")
    if (
        not parsed.hostname or parsed.query or parsed.fragment or
        parsed.username is not None or parsed.password is not None or
        parsed_port is not None and not 1 <= parsed_port <= 65535
    ):
        raise ValueError("The push relay URL is not valid.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise ValueError("The push relay URL must use HTTPS.")
    return value


def _canonical_json(payload):
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _signed_request(url, method, subscription, payload):
    body = _canonical_json(payload)
    timestamp = str(int(time.time()))
    signed = timestamp.encode("ascii") + b"\n" + body
    signature = hmac.new(
        subscription["send_secret"].encode("utf-8"), signed, hashlib.sha256
    ).hexdigest()
    return Request(
        url,
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "X-OSPy-Subscription": subscription["subscription_id"],
            "X-OSPy-Timestamp": timestamp,
            "X-OSPy-Signature": signature,
        },
    )


class PushDispatcher(object):
    def __init__(self):
        self._queue = queue.Queue(maxsize=QUEUE_LIMIT)
        self._lock = threading.RLock()
        self._thread = None
        self._sent = 0
        self._failed = 0
        self._dropped = 0

    def status(self):
        config = mobile_store.push_config()
        with self._lock:
            return {
                "enabled": config["enabled"],
                "configured": bool(config["relay_url"]),
                "relay_url": config["relay_url"],
                "queue_size": self._queue.qsize(),
                "sent": self._sent,
                "failed": self._failed,
                "dropped": self._dropped,
            }

    def enqueue_notification(self, notification):
        config = mobile_store.push_config()
        if not config["enabled"] or not config["relay_url"]:
            return False
        item = dict(notification)
        item["category"] = notification_category(
            item.get("event_type", ""), item.get("code", "")
        )
        return self._enqueue(("notification", item))

    def enqueue_test(self, device_id, title="OSPy", message=""):
        config = mobile_store.push_config()
        subscription = mobile_store.push_subscription(device_id, include_secret=True)
        if not config["enabled"] or not config["relay_url"] or not subscription:
            return False
        notification = {
            "id": "test-{}".format(int(time.time() * 1000)),
            "event_type": "system",
            "severity": "info",
            "code": "test_notification",
            "title": title,
            "message": message,
            "data": {},
            "category": "other",
            "device_id": device_id,
        }
        return self._enqueue(("direct", subscription, notification))

    def unregister(self, device_id):
        subscription = mobile_store.push_subscription(device_id, include_secret=True)
        mobile_store.delete_push_subscription(device_id)
        config = mobile_store.push_config()
        if subscription and config["relay_url"]:
            self._enqueue(("unregister", config["relay_url"], subscription))
        return bool(subscription)

    def _enqueue(self, item):
        self._start()
        try:
            self._queue.put_nowait(item)
            return True
        except queue.Full:
            with self._lock:
                self._dropped += 1
            log.error("api/v1/push", "Push delivery queue is full.")
            return False

    def _start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._run, name="OSPy push dispatcher", daemon=True
            )
            self._thread.start()

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item[0] == "notification":
                    self._deliver_notification(item[1])
                elif item[0] == "direct":
                    self._deliver(item[1], item[2])
                elif item[0] == "unregister":
                    self._deliver_unregister(item[1], item[2])
            except Exception as error:
                log.error("api/v1/push", "Push worker error: {}".format(
                    type(error).__name__
                ))
            finally:
                self._queue.task_done()

    def _deliver_notification(self, notification):
        config = mobile_store.push_config()
        if not config["enabled"] or not config["relay_url"]:
            return
        subscriptions = mobile_store.push_subscriptions(
            notification["category"], include_secret=True
        )
        for subscription in subscriptions:
            self._deliver(subscription, notification, config["relay_url"])

    def _deliver(self, subscription, notification, relay_url=None):
        relay_url = relay_url or mobile_store.push_config()["relay_url"]
        payload = {
            "instance_id": mobile_store.instance_id(),
            "notification_id": notification.get("id"),
            "event_type": notification.get("event_type", "system"),
            "severity": notification.get("severity", "info"),
            "code": notification.get("code", "notification"),
            "title": notification.get("title", "OSPy"),
            "message": notification.get("message", ""),
            "data": notification.get("data") or {},
        }
        try:
            request = _signed_request(
                relay_url + "/v1/send", "POST", subscription, payload
            )
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                if response.status < 200 or response.status >= 300:
                    raise RuntimeError("HTTP {}".format(response.status))
            mobile_store.record_push_result(subscription["device_id"], True)
            with self._lock:
                self._sent += 1
        except (HTTPError, URLError, OSError, RuntimeError) as error:
            reason = self._safe_error(error)
            mobile_store.record_push_result(
                subscription["device_id"], False, reason
            )
            with self._lock:
                self._failed += 1
            log.error("api/v1/push", "Push delivery failed: {}".format(reason))

    def _deliver_unregister(self, relay_url, subscription):
        payload = {"instance_id": mobile_store.instance_id()}
        url = relay_url + "/v1/subscriptions/" + quote(
            subscription["subscription_id"], safe=""
        )
        try:
            request = _signed_request(url, "DELETE", subscription, payload)
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                if response.status < 200 or response.status >= 300:
                    raise RuntimeError("HTTP {}".format(response.status))
        except (HTTPError, URLError, OSError, RuntimeError) as error:
            log.error(
                "api/v1/push",
                "Push unregistration failed: {}".format(self._safe_error(error)),
            )

    @staticmethod
    def _safe_error(error):
        if isinstance(error, HTTPError):
            return "relay_http_{}".format(error.code)
        if isinstance(error, URLError):
            return "relay_connection_{}".format(type(error.reason).__name__)
        return "relay_error_{}".format(type(error).__name__)


push_dispatcher = PushDispatcher()
