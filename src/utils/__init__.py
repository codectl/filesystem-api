import os
import pwd
import functools

from flask_restful import abort
from werkzeug.http import HTTP_STATUS_CODES

from src.schemas.serializers.http import HttpResponseSchema
from src.settings import oas


def convert_bytes(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:.0f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.0f} Y{suffix}"


def normpath(path):
    return os.path.join(os.path.sep, path.strip(os.path.sep))


def http_response(code: int, message="", serialize=True, **kwargs):
    response = oas.HttpResponse(
        code=code, reason=HTTP_STATUS_CODES[code], message=message
    )
    if serialize:
        return HttpResponseSchema(**kwargs).dump(response)
    return response


def abort_with(code: int, message="", **kwargs):
    abort(code, **http_response(code, message=message, **kwargs))


def user_uid(username):
    return pwd.getpwnam(username).pw_uid


def user_gid(username):
    return pwd.getpwnam(username).pw_gid


def impersonate(func):
    """Decorator to run a routing under user privileges."""

    class user_ctx:
        def __init__(self, username):
            self.username = username
            self.uid = os.getuid()
            self.gid = os.getuid()
            self.ctx_uid = self.uid
            self.ctx_gid = self.gid

        def __enter__(self):
            try:
                self.ctx_uid = user_uid(self.username)
                self.ctx_gid = user_gid(self.username)
                os.setuid(self.ctx_uid)
                os.setgid(self.ctx_gid)
            except (KeyError, TypeError):
                pass  # suppress missing username
            except PermissionError:
                pass  # suppress missing privileges

        def __exit__(self, exc_type, exc_value, exc_traceback):
            if self.uid != self.ctx_uid or self.gid != self.ctx_gid:
                os.setuid(self.uid)
                os.setgid(self.gid)

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with user_ctx(self.username):
            return func(self, *args, **kwargs)

    return wrapper
