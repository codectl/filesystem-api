import os
import pwd

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
