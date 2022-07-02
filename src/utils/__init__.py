import os
import pwd
import subprocess

from flask_restful import abort
from werkzeug.http import HTTP_STATUS_CODES

from src.schemas.serlializers.http import HttpResponseSchema
from src.settings import oas


def convert_bytes(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:.0f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def normpath(path):
    return os.path.normpath(f"/{path.strip('/')}")


def shell(cmd, universal_newlines=True, **kwargs):
    popen = subprocess.Popen(
        cmd.split(),
        stdin=kwargs.pop("stdin", subprocess.PIPE),
        stdout=kwargs.pop("stdout", subprocess.PIPE),
        stderr=kwargs.pop("stderr", subprocess.PIPE),
        universal_newlines=universal_newlines,
        **kwargs,
    )

    stdout, stderr = popen.communicate()
    if popen.returncode > 0:
        raise subprocess.CalledProcessError(
            returncode=popen.returncode, cmd=cmd, stderr=stderr
        )
    return stdout


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
