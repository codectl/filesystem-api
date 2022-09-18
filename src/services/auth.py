import os
import functools
import sys
import traceback

from multiprocessing import Process, Queue, get_context

from src import utils

__all__ = ("AuthSvc", "impersonate")


class AuthSvc:
    @staticmethod
    def authenticate(username, password):
        return True


def target(queue, el):
    queue.put(el)


def process():
    def wrapper(fn):
        ctx = get_context("spawn")
        queue = ctx.Queue(maxsize=1)

        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            ret = fn(*args, **kwargs)
            ctx.Process(target=target, args=(queue, ret)).start()
            return queue.get()

        return decorated

    return wrapper


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

        def __exit__(self, exc_type, exc_value, exc_traceback):
            pass

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
                return func(*args, **kwargs)

        return decorated

    return wrapper
