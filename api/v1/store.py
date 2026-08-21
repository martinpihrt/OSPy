"""Persistent security and mobile-client state for API v1."""

import hashlib
import datetime
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid


SCHEMA_VERSION = 2
DEFAULT_REFRESH_LIFETIME = 30 * 24 * 60 * 60
# A mobile process can be terminated after OSPy has rotated a refresh token but
# before Android has durably stored the replacement (for example during a
# Google Play update). Permit exactly one retry of that just-replaced token.
REFRESH_RECOVERY_GRACE = 5 * 60
DEFAULT_PUSH_RELAY_URL = (
    "https://ospy-push-relay-668635864569.europe-west1.run.app"
)
MAX_NOTIFICATIONS = 1000
MAX_OPERATIONS = 500
PUSH_CATEGORIES = (
    "station_started", "station_stopped", "rain", "diagnostics",
    "updates", "automation", "other",
)


class _ClosingConnection(sqlite3.Connection):
    """Commit or roll back like sqlite3.Connection, then release the file."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super(_ClosingConnection, self).__exit__(
                exc_type, exc_value, traceback
            )
        finally:
            self.close()


def _data_dir():
    return os.path.abspath(os.environ.get("OSPY_DATA_DIR", os.path.join("ospy", "data")))


def _token_hash(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _iso_timestamp(value):
    if value is None:
        return None
    return datetime.datetime.fromtimestamp(
        float(value), datetime.timezone.utc
    ).isoformat()


class MobileStore(object):
    """Small SQLite store kept separate from authoritative OSPy settings."""

    def __init__(self):
        self._lock = threading.RLock()
        self._initialized = set()

    @property
    def path(self):
        return os.path.join(_data_dir(), "api_v1.sqlite3")

    def _connect(self):
        path = self.path
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        connection = sqlite3.connect(
            path, timeout=10, factory=_ClosingConnection
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        self._initialize(connection, path)
        return connection

    def _initialize(self, connection, path):
        with self._lock:
            if path in self._initialized:
                return
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    name TEXT NOT NULL,
                    app_version TEXT NOT NULL DEFAULT '',
                    created REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    revoked REAL
                );
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    scopes TEXT NOT NULL,
                    created REAL NOT NULL,
                    expires REAL NOT NULL,
                    last_used REAL NOT NULL,
                    revoked REAL,
                    replaced_by TEXT
                );
                CREATE TABLE IF NOT EXISTS login_challenges (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    expires REAL NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created REAL NOT NULL,
                    acknowledged REAL
                );
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    result TEXT NOT NULL DEFAULT '{}',
                    error TEXT NOT NULL DEFAULT '',
                    created REAL NOT NULL,
                    updated REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    device_id TEXT PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
                    subscription_id TEXT NOT NULL UNIQUE,
                    send_secret TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    categories TEXT NOT NULL,
                    registered REAL NOT NULL,
                    updated REAL NOT NULL,
                    last_success REAL,
                    last_failure REAL,
                    failure_reason TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS push_subscriptions_enabled
                    ON push_subscriptions(enabled);
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            connection.commit()
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            self._initialized.add(path)

    def meta(self, key, factory=None):
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM meta WHERE key=?", (key,)
            ).fetchone()
            if row is not None:
                return row["value"]
            if factory is None:
                return None
            value = str(factory())
            connection.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?)", (key, value)
            )
            return value

    def set_meta(self, key, value):
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO meta(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (str(key), str(value)),
            )

    def push_config(self):
        relay_url = self.meta(
            "push_relay_url", lambda: DEFAULT_PUSH_RELAY_URL
        ).strip()
        return {
            "enabled": self.meta("push_enabled", lambda: "0") == "1",
            "relay_url": relay_url or DEFAULT_PUSH_RELAY_URL,
        }

    def set_push_config(self, enabled, relay_url):
        with self._lock, self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO meta(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (
                    ("push_enabled", "1" if enabled else "0"),
                    (
                        "push_relay_url",
                        str(relay_url or "").strip().rstrip("/"),
                    ),
                ),
            )

    def instance_id(self):
        return self.meta("instance_id", lambda: str(uuid.uuid4()))

    def signing_secret(self):
        return self.meta("signing_secret", lambda: secrets.token_urlsafe(48))

    def issue_refresh_token(
            self, username, role, scopes, device_id, device_name,
            app_version="", lifetime=DEFAULT_REFRESH_LIFETIME):
        now = time.time()
        device_id = str(device_id or uuid.uuid4())
        token_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(48)
        scopes_json = json.dumps(sorted(set(scopes)), separators=(",", ":"))
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT username FROM devices WHERE id=?", (device_id,)
            ).fetchone()
            if existing is not None and existing["username"] != username:
                # A client-supplied identifier must never take over a device
                # paired by another account.
                device_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO devices(
                    id, username, role, name, app_version, created, last_seen, revoked
                ) VALUES(?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    role=excluded.role,
                    name=excluded.name,
                    app_version=excluded.app_version,
                    last_seen=excluded.last_seen,
                    revoked=NULL
                """,
                (
                    device_id, username, role, str(device_name or "Android"),
                    str(app_version or ""), now, now,
                ),
            )
            connection.execute(
                """
                UPDATE refresh_tokens
                SET revoked=?, replaced_by=NULL
                WHERE device_id=?
                """,
                (now, device_id),
            )
            connection.execute(
                """
                INSERT INTO refresh_tokens(
                    id, device_id, token_hash, scopes, created, expires,
                    last_used, revoked, replaced_by
                ) VALUES(?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    token_id, device_id, _token_hash(token), scopes_json,
                    now, now + lifetime, now,
                ),
            )
        return {
            "id": token_id,
            "token": token,
            "device_id": device_id,
            "expires": now + lifetime,
            "scopes": json.loads(scopes_json),
        }

    def rotate_refresh_token(self, token, lifetime=DEFAULT_REFRESH_LIFETIME):
        now = time.time()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT r.*, d.username, d.role, d.name, d.app_version, d.revoked AS device_revoked
                FROM refresh_tokens r
                JOIN devices d ON d.id=r.device_id
                WHERE r.token_hash=?
                """,
                (_token_hash(token),),
            ).fetchone()
            recovery_retry = bool(
                row is not None and row["replaced_by"] and
                row["revoked"] is not None and
                now - row["revoked"] <= REFRESH_RECOVERY_GRACE and
                abs(row["last_used"] - row["revoked"]) < 0.001
            )
            if (
                row is None or row["device_revoked"] is not None or
                row["expires"] <= now or
                (row["revoked"] is not None and not recovery_retry) or
                (row["replaced_by"] and not recovery_retry)
            ):
                return None
            replacement_id = str(uuid.uuid4())
            replacement_token = secrets.token_urlsafe(48)
            replacement_expires = now + lifetime
            connection.execute(
                """
                INSERT INTO refresh_tokens(
                    id, device_id, token_hash, scopes, created, expires,
                    last_used, revoked, replaced_by
                ) VALUES(?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    replacement_id, row["device_id"],
                    _token_hash(replacement_token), row["scopes"], now,
                    replacement_expires, now,
                ),
            )
            if recovery_retry:
                # Mark the recovery attempt as consumed without extending the
                # original grace window. A second replay is rejected.
                connection.execute(
                    "UPDATE refresh_tokens SET replaced_by=?, last_used=? WHERE id=?",
                    (
                        replacement_id,
                        max(now, row["revoked"] + 1.0),
                        row["id"],
                    ),
                )
            else:
                connection.execute(
                    "UPDATE refresh_tokens SET revoked=?, replaced_by=?, last_used=? WHERE id=?",
                    (now, replacement_id, now, row["id"]),
                )
            return {
                "id": replacement_id,
                "token": replacement_token,
                "device_id": row["device_id"],
                "expires": replacement_expires,
                "scopes": json.loads(row["scopes"]),
                "username": row["username"],
                "role": row["role"],
            }

    def active_token_session(self, token_id, device_id):
        now = time.time()
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT r.id, r.scopes, r.expires, r.revoked, r.replaced_by,
                       d.id AS device_id, d.username, d.role, d.revoked AS device_revoked
                FROM refresh_tokens r
                JOIN devices d ON d.id=r.device_id
                WHERE r.id=? AND d.id=?
                """,
                (token_id, device_id),
            ).fetchone()
            if (
                row is None or
                (row["revoked"] is not None and row["replaced_by"] is None) or
                row["device_revoked"] is not None or row["expires"] <= now
            ):
                return None
            connection.execute(
                "UPDATE devices SET last_seen=? WHERE id=?", (now, device_id)
            )
            return {
                "username": row["username"],
                "role": row["role"],
                "scopes": json.loads(row["scopes"]),
                "device_id": row["device_id"],
                "token_id": row["id"],
            }

    def revoke_refresh_token(self, token_id):
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT device_id FROM refresh_tokens WHERE id=?", (token_id,)
            ).fetchone()
            if row is not None:
                connection.execute(
                    "UPDATE refresh_tokens SET revoked=?, replaced_by=NULL WHERE device_id=?",
                    (time.time(), row["device_id"]),
                )

    def revoke_device(self, device_id):
        now = time.time()
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE devices SET revoked=? WHERE id=? AND revoked IS NULL",
                (now, device_id),
            )
            connection.execute(
                "UPDATE refresh_tokens SET revoked=? WHERE device_id=? AND revoked IS NULL",
                (now, device_id),
            )
            connection.execute(
                "DELETE FROM push_subscriptions WHERE device_id=?", (device_id,)
            )

    def delete_revoked_device(self, device_id):
        """Permanently delete one already-revoked device and its token history."""
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT revoked FROM devices WHERE id=?", (device_id,)
            ).fetchone()
            if row is None or row["revoked"] is None:
                return False
            connection.execute("DELETE FROM devices WHERE id=?", (device_id,))
            return True

    def delete_all_revoked_devices(self):
        """Permanently delete all revoked devices and return their count."""
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM devices WHERE revoked IS NOT NULL"
            ).fetchone()
            count = int(row["count"])
            if count:
                connection.execute(
                    "DELETE FROM devices WHERE revoked IS NOT NULL"
                )
            return count

    def devices(self, username=None):
        query = "SELECT * FROM devices"
        values = ()
        if username:
            query += " WHERE username=?"
            values = (username,)
        query += " ORDER BY last_seen DESC"
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "name": row["name"],
                "app_version": row["app_version"],
                "created": _iso_timestamp(row["created"]),
                "last_seen": _iso_timestamp(row["last_seen"]),
                "revoked": _iso_timestamp(row["revoked"]),
            }
            for row in rows
        ]

    @staticmethod
    def _push_row(row, include_secret=False):
        if row is None:
            return None
        result = {
            "device_id": row["device_id"],
            "subscription_id": row["subscription_id"],
            "enabled": bool(row["enabled"]),
            "categories": json.loads(row["categories"] or "[]"),
            "registered": _iso_timestamp(row["registered"]),
            "updated": _iso_timestamp(row["updated"]),
            "last_success": _iso_timestamp(row["last_success"]),
            "last_failure": _iso_timestamp(row["last_failure"]),
            "failure_reason": row["failure_reason"],
        }
        if include_secret:
            result["send_secret"] = row["send_secret"]
        return result

    def push_subscription(self, device_id, include_secret=False):
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM push_subscriptions WHERE device_id=?", (device_id,)
            ).fetchone()
        return self._push_row(row, include_secret)

    def save_push_subscription(
            self, device_id, subscription_id, send_secret, enabled=True,
            categories=None):
        categories = sorted(set(
            PUSH_CATEGORIES if categories is None else categories
        ))
        if not categories or any(item not in PUSH_CATEGORIES for item in categories):
            raise ValueError("Invalid push category")
        now = time.time()
        categories_json = json.dumps(categories, separators=(",", ":"))
        with self._lock, self._connect() as connection:
            device = connection.execute(
                "SELECT revoked FROM devices WHERE id=?", (device_id,)
            ).fetchone()
            if device is None or device["revoked"] is not None:
                raise KeyError("Device does not exist or is revoked")
            owner = connection.execute(
                "SELECT device_id FROM push_subscriptions WHERE subscription_id=?",
                (str(subscription_id),),
            ).fetchone()
            if owner is not None and owner["device_id"] != device_id:
                raise ValueError("Push subscription is already assigned")
            connection.execute(
                """
                INSERT INTO push_subscriptions(
                    device_id, subscription_id, send_secret, enabled, categories,
                    registered, updated, last_success, last_failure, failure_reason
                ) VALUES(?, ?, ?, ?, ?, ?, ?, NULL, NULL, '')
                ON CONFLICT(device_id) DO UPDATE SET
                    subscription_id=excluded.subscription_id,
                    send_secret=excluded.send_secret,
                    enabled=excluded.enabled,
                    categories=excluded.categories,
                    updated=excluded.updated,
                    last_failure=NULL,
                    failure_reason=''
                """,
                (
                    device_id, str(subscription_id), str(send_secret),
                    1 if enabled else 0, categories_json, now, now,
                ),
            )
        return self.push_subscription(device_id)

    def update_push_preferences(self, device_id, enabled, categories):
        categories = sorted(set(categories or []))
        if not categories or any(item not in PUSH_CATEGORIES for item in categories):
            raise ValueError("Invalid push category")
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE push_subscriptions
                SET enabled=?, categories=?, updated=?
                WHERE device_id=?
                """,
                (
                    1 if enabled else 0,
                    json.dumps(categories, separators=(",", ":")),
                    time.time(), device_id,
                ),
            )
            if cursor.rowcount < 1:
                raise KeyError("Push subscription does not exist")
        return self.push_subscription(device_id)

    def delete_push_subscription(self, device_id):
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM push_subscriptions WHERE device_id=?", (device_id,)
            )

    def push_subscriptions(self, category=None, include_secret=False):
        query = """
            SELECT p.* FROM push_subscriptions p
            JOIN devices d ON d.id=p.device_id
            WHERE p.enabled=1 AND d.revoked IS NULL
        """
        with self._lock, self._connect() as connection:
            rows = connection.execute(query).fetchall()
        items = [self._push_row(row, include_secret) for row in rows]
        if category:
            items = [item for item in items if category in item["categories"]]
        return items

    def devices_with_push(self):
        devices = self.devices()
        subscriptions = {
            item["device_id"]: item for item in self.push_subscriptions()
        }
        # Disabled subscriptions are intentionally included in administration.
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT * FROM push_subscriptions").fetchall()
        subscriptions.update({
            row["device_id"]: self._push_row(row) for row in rows
        })
        for device in devices:
            device["push"] = subscriptions.get(device["id"])
        return devices

    def record_push_result(self, device_id, success, reason=""):
        now = time.time()
        with self._lock, self._connect() as connection:
            if success:
                connection.execute(
                    """
                    UPDATE push_subscriptions
                    SET last_success=?, failure_reason='' WHERE device_id=?
                    """,
                    (now, device_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE push_subscriptions
                    SET last_failure=?, failure_reason=? WHERE device_id=?
                    """,
                    (now, str(reason or "")[:240], device_id),
                )

    def create_login_challenge(self, username, nonce, code_hash, expires):
        challenge_id = str(uuid.uuid4())
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO login_challenges(
                    id, username, nonce, code_hash, expires, attempts, created
                ) VALUES(?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    challenge_id, username, nonce, code_hash,
                    float(expires), time.time(),
                ),
            )
            connection.execute(
                "DELETE FROM login_challenges WHERE expires<?", (time.time(),)
            )
        return challenge_id

    def login_challenge(self, challenge_id, username):
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM login_challenges WHERE id=? AND username=?",
                (challenge_id, username),
            ).fetchone()
            if row is None or row["expires"] <= time.time() or row["attempts"] >= 5:
                return None
            connection.execute(
                "UPDATE login_challenges SET attempts=attempts+1 WHERE id=?",
                (challenge_id,),
            )
            return dict(row)

    def consume_login_challenge(self, challenge_id):
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM login_challenges WHERE id=?", (challenge_id,)
            )

    def add_notification(
            self, event_type, severity, code, title, message="", data=None):
        now = time.time()
        payload = json.dumps(data or {}, separators=(",", ":"), ensure_ascii=False)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO notifications(
                    event_type, severity, code, title, message, data, created, acknowledged
                ) VALUES(?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (event_type, severity, code, title, message, payload, now),
            )
            notification_id = cursor.lastrowid
            connection.execute(
                """
                DELETE FROM notifications
                WHERE id IN (
                    SELECT id FROM notifications ORDER BY id DESC LIMIT -1 OFFSET ?
                )
                """,
                (MAX_NOTIFICATIONS,),
            )
        return notification_id

    def notifications(self, cursor=None, limit=100, unread=False):
        limit = max(1, min(int(limit or 100), 500))
        clauses = []
        values = []
        if cursor:
            clauses.append("id < ?")
            values.append(int(cursor))
        if unread:
            clauses.append("acknowledged IS NULL")
        query = "SELECT * FROM notifications"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        values.append(limit + 1)
        with self._lock, self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        items = []
        for row in rows:
            item = dict(row)
            item["data"] = json.loads(item["data"] or "{}")
            item["created"] = _iso_timestamp(item["created"])
            item["acknowledged"] = _iso_timestamp(item["acknowledged"])
            items.append(item)
        return {
            "items": items,
            "next_cursor": str(items[-1]["id"]) if has_more and items else None,
            "has_more": has_more,
        }

    def unread_notification_count(self):
        with self._lock, self._connect() as connection:
            return int(connection.execute(
                "SELECT COUNT(*) FROM notifications WHERE acknowledged IS NULL"
            ).fetchone()[0])

    def acknowledge_notification(self, notification_id=None):
        now = time.time()
        with self._lock, self._connect() as connection:
            if notification_id is None:
                connection.execute(
                    "UPDATE notifications SET acknowledged=? WHERE acknowledged IS NULL",
                    (now,),
                )
            else:
                connection.execute(
                    "UPDATE notifications SET acknowledged=? WHERE id=?",
                    (now, int(notification_id)),
                )

    def create_operation(self, kind):
        operation_id = str(uuid.uuid4())
        now = time.time()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO operations(id, kind, status, progress, result, error, created, updated)
                VALUES(?, ?, 'pending', 0, '{}', '', ?, ?)
                """,
                (operation_id, kind, now, now),
            )
            connection.execute(
                """
                DELETE FROM operations
                WHERE id IN (
                    SELECT id FROM operations ORDER BY updated DESC LIMIT -1 OFFSET ?
                )
                """,
                (MAX_OPERATIONS,),
            )
        return operation_id

    def update_operation(
            self, operation_id, status=None, progress=None, result=None, error=None):
        fields = ["updated=?"]
        values = [time.time()]
        for name, value in (
            ("status", status), ("progress", progress), ("error", error)
        ):
            if value is not None:
                fields.append(name + "=?")
                values.append(value)
        if result is not None:
            fields.append("result=?")
            values.append(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
        values.append(operation_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE operations SET {} WHERE id=?".format(", ".join(fields)),
                values,
            )

    def operation(self, operation_id):
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM operations WHERE id=?", (operation_id,)
            ).fetchone()
        if row is None:
            return None
        value = dict(row)
        value["result"] = json.loads(value["result"] or "{}")
        value["created"] = _iso_timestamp(value["created"])
        value["updated"] = _iso_timestamp(value["updated"])
        return value


mobile_store = MobileStore()
