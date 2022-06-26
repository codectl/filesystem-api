from functools import wraps

from flask import g, request
from flask_restful import abort
from werkzeug.local import LocalProxy

from src.services.auth import AuthSvc


# proxy to get username from g
current_username = LocalProxy(lambda: g.username)


def requires_auth(schemes=("basic",)):
    """Validate endpoint against given authorization schemes.
    Fail if authorization properties are missing or are invalid."""

    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if "basic" in schemes:
                auth = request.authorization
                if auth and AuthSvc.authenticate(
                    username=auth.username, password=auth.password
                ):
                    g.username = auth.username
                    return func(*args, **kwargs)
            elif "bearer" in schemes:
                raise NotImplementedError

            abort(401, code=401, reason="Unauthorized")

        return decorated

    return wrapper
