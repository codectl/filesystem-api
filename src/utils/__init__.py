import os
import stat
import subprocess

from flask_restful import abort
from werkzeug.http import HTTP_STATUS_CODES

from src.schemas.serlializers.http import HttpResponseSchema
from src.settings import oas


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


def isfile(mode):
    return stat.S_ISREG(mode or 0)


def isdir(mode):
    return stat.S_ISDIR(mode or 0)


def file_mode(stats):
    """Return first character from a stat string like '-rwx'."""
    if not stats or not isinstance(stats, str):
        return None
    permissions = next(iter(stats.split()), "")
    char = next(iter(permissions), None)
    if char == "-":
        return stat.S_IFREG
    elif char == "d":
        return stat.S_IFDIR
    return 0


def http_response(code: int, message="", serialize=True, **kwargs):
    response = oas.HttpResponse(
        code=code, reason=HTTP_STATUS_CODES[code], message=message
    )
    if serialize:
        return HttpResponseSchema(**kwargs).dump(response)
    return response


def abort_with(code: int, message=""):
    abort(code, **http_response(code, message=message))
