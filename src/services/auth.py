import os
import functools
import inspect

from src import utils

__all__ = ("AuthSvc", "impersonate")


class AuthSvc:
    @staticmethod
    def authenticate(username, password):
        return True


def impersonate(username=None):
    """Run a routing under user privileges."""

    def wrapper(func):
        class user_ctx:
            def __init__(self, usrname):
                self.username = usrname
                self.uid = os.getuid()
                self.gid = os.getuid()
                self.ctx_uid = self.uid
                self.ctx_gid = self.gid

            def __enter__(self):
                try:
                    self.ctx_uid = utils.user_uid(self.username)
                    self.ctx_gid = utils.user_gid(self.username)
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
        def decorated(*args, **kwargs):
            self = next(iter(args), None)
            name = (
                getattr(self, "username", None)
                if not username and inspect.isclass(self)
                else username
            )
            with user_ctx(name):
                return func(*args, **kwargs)

        return decorated

    return wrapper
