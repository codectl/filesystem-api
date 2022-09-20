import os
import functools
import re
import sys
import traceback

from multiprocessing import Process, Queue, get_context

from src import utils

__all__ = ("AuthSvc", "as_user")


class AuthSvc:
    @staticmethod
    def authenticate(username, password):
        return True


def target(queue, fn, *args, **kwargs):
    queue.put(fn(*args, **kwargs))


def as_user(arg=None, username=None):
    """Run a routing under user privileges."""

    class run_as:
        def __init__(self, user):
            self.user = user

        def __enter__(self):
            try:
                os.setuid(utils.user_uid(self.user))
                os.setgid(utils.user_gid(self.user))
            except (KeyError, TypeError):
                pass  # suppress missing username
            except PermissionError:
                pass  # suppress missing privileges

        def __exit__(self, exc_type, exc_value, exc_traceback):
            pass

    def fn_wrapper(fn):
        ctx = get_context("spawn")
        queue = ctx.Queue(maxsize=1)

        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            self = next(iter(args), None)
            user = (
                getattr(self, "username", None)
                if not username and hasattr(self, "__class__")
                else username
            )

            with run_as(user=user):
                ctx.Process(target=target, args=(queue, fn, *args), kwargs=kwargs).start()
                return queue.get()

        return decorated

    def cls_wrapper(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr) and not re.match(r"__\w__", attr)):
                setattr(cls, attr, fn_wrapper(getattr(cls, attr)))
        return cls

    return cls_wrapper(arg) if callable(arg) else cls_wrapper
