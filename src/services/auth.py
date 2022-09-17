import os
import functools

from multiprocessing import Process

from src import utils

__all__ = ("AuthSvc", "impersonate")


class AuthSvc:
    @staticmethod
    def authenticate(username, password):
        return True


def impersonate(username=None):
    """Run a routing under user privileges."""

    class UserCtx:
        def __init__(self, usrname):
            self.username = usrname

        def __enter__(self):
            try:
                os.setuid(utils.user_uid(self.username))
                os.setgid(utils.user_gid(self.username))
            except (KeyError, TypeError):
                pass  # suppress missing username
            except PermissionError:
                pass  # suppress missing privileges

    def wrapper(func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            self = next(iter(args), None)
            name = (
                getattr(self, "username", None)
                if not username and hasattr(self, "__class__")
                else username
            )

            with UserCtx(usrname=name):
                p = Process(target=func, args=args, kwargs=kwargs)
                p.start()
                p.join()

        return decorated

    return wrapper
