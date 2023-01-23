import os
import pwd
from pathlib import Path

from apispec_plugins.types import HTTPResponse
from flask_restful import abort
from werkzeug.http import HTTP_STATUS_CODES

from src.schemas.serializers.http import HttpResponseSchema


def convert_bytes(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:.0f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.0f} Y{suffix}"


def normpath(path) -> Path:
    return Path(os.path.join(os.path.sep, path.strip(os.path.sep)))


def http_response(code: int, description="", serialize=True, **kwargs):
    reason = HTTP_STATUS_CODES[code]
    description = f"{reason}: {description}" if description else reason
    response = HTTPResponse(code=code, description=description)
    if serialize:
        return HttpResponseSchema(**kwargs).dump(response)
    return response


def abort_with(code: int, description="", **kwargs):
    abort(code, **http_response(code, description=description, **kwargs))


def user_uid(username):
    return pwd.getpwnam(username).pw_uid


def user_gid(username):
    return pwd.getpwnam(username).pw_gid


def system_username():
    return pwd.getpwuid(os.getuid()).pw_name
