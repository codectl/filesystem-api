import multiprocessing
import ssl

from gunicorn.app.base import BaseApplication
from gunicorn.workers.sync import SyncWorker

from src.app import create_app
from src.settings.env import env


class WsgiAppSyncWorker(SyncWorker):
    def handle_request(self, listener, req, client, addr):
        """Handles each incoming request after a client has been authenticated."""
        subject = dict([i for subtuple in client.getpeercert().get("subject") for i in subtuple])
        issuer = dict([i for subtuple in client.getpeercert().get("issuer") for i in subtuple])
        headers = dict(req.headers)
        headers["X-USER"] = subject.get("commonName")
        not_before = client.getpeercert().get("notBefore")
        not_after = client.getpeercert().get("notAfter")
        headers["X-NOT_BEFORE"] = ssl.cert_time_to_seconds(not_before)
        headers["X-NOT_AFTER"] = ssl.cert_time_to_seconds(not_after)
        headers["X-ISSUER"] = issuer["commonName"]

        req.headers = list(headers.items())
        super().handle_request(listener, req, client, addr)


class WsgiApplication(BaseApplication):
    def __init__(self, app, opts=None):
        self.opts = opts or {}
        self.application = app
        super().__init__()

    def init(self, parser, opts, args):
        return super().init(parser, opts, args)

    def load_config(self):
        config = {
            key: value for key, value in self.opts.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


if __name__ == "__main__":
    environ = env.str("ENV", "development")
    if environ not in ["development", "production", "testing"]:
        raise EnvironmentError

    wsgi_app = create_app(environ=environ)
    options = {
        "bind": env.str("WEB_BIND", "0.0.0.0:8080"),
        "reload": env.bool("WEB_RELOAD", False),
        "workers": env.int("WEB_CONCURRENCY", number_of_workers()),
        "threads": env.int("PYTHON_MAX_THREADS", 1),
        "loglevel": "debug",
        "worker_class": "src.wsgi.WsgiAppSyncWorker",
        "cert_reqs": ssl.VerifyMode.CERT_OPTIONAL,
        "do_handshake_on_connect": True,
    }
    WsgiApplication(wsgi_app, options).run()
