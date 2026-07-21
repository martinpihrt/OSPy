"""
Small fallback for the parts of the removed stdlib cgi module used by web.py.

Python 3.13 removed cgi. OSPy only needs FieldStorage for query strings,
urlencoded forms, and multipart form uploads, so this module implements that
limited surface instead of pulling in the whole retired module.
"""

from email.parser import BytesParser
from email.policy import default as email_policy
from io import BytesIO
from urllib.parse import parse_qsl


class FieldStorage:
    def __init__(self, fp=None, environ=None, keep_blank_values=False, **kwargs):
        self.fp = fp
        self.environ = environ or {}
        self.keep_blank_values = keep_blank_values
        self.name = kwargs.get("name")
        self.filename = kwargs.get("filename")
        self.value = kwargs.get("value", "")
        self.file = kwargs.get("file")
        self.list = kwargs.get("list")

        if self.list is None and kwargs.get("_field") is None:
            self.list = []
            self._parse()

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        return key in self.keys()

    def __getitem__(self, key):
        values = [field for field in self.list if field.name == key]
        if not values:
            raise KeyError(key)
        if len(values) == 1:
            return values[0]
        return values

    def keys(self):
        keys = []
        for field in self.list or []:
            if field.name not in keys:
                keys.append(field.name)
        return keys

    def make_file(self, binary=None):
        return BytesIO()

    def _parse(self):
        method = self.environ.get("REQUEST_METHOD", "GET").upper()
        content_type = self.environ.get("CONTENT_TYPE", "")

        if method == "GET":
            self._add_urlencoded(self.environ.get("QUERY_STRING", ""))
        elif content_type.lower().startswith("multipart/"):
            self._add_multipart(content_type, self._read_body())
        else:
            body = self._read_body().decode("utf-8", "replace")
            self._add_urlencoded(body)

    def _read_body(self):
        if not self.fp:
            return b""
        try:
            length = int(self.environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0
        data = self.fp.read(length) if length else self.fp.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        return data

    def _add_urlencoded(self, data):
        for name, value in parse_qsl(data, keep_blank_values=bool(self.keep_blank_values)):
            self.list.append(self._field(name=name, value=value))

    def _add_multipart(self, content_type, body):
        header = (
            "Content-Type: {}\r\n"
            "MIME-Version: 1.0\r\n"
            "\r\n"
        ).format(content_type).encode("utf-8")
        message = BytesParser(policy=email_policy).parsebytes(header + body)

        if not message.is_multipart():
            return

        for part in message.iter_parts():
            if part.get_content_disposition() != "form-data":
                continue

            name = part.get_param("name", header="content-disposition")
            if not name:
                continue

            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename is None:
                charset = part.get_content_charset() or "utf-8"
                value = payload.decode(charset, "replace")
                self.list.append(self._field(name=name, value=value))
            else:
                self.list.append(
                    self._field(
                        name=name,
                        filename=filename,
                        value=payload,
                        file=BytesIO(payload),
                    )
                )

    @classmethod
    def _field(cls, name, value, filename=None, file=None):
        return cls(
            name=name,
            filename=filename,
            value=value,
            file=file,
            list=[],
            _field=True,
        )
