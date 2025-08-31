import multiprocessing
import argparse
import os

from gunicorn.app.wsgiapp import WSGIApplication

parser = argparse.ArgumentParser(description="Start DRF-Game server")

parser.add_argument("--host", type=str,default='0.0.0.0', help="ip address.")
parser.add_argument("--port", type=str,default="8000", help="port number.")
parser.add_argument("--workers", type=int, default=1, help="Number of workers.")

args = parser.parse_args()

class StandaloneApplication(WSGIApplication):
    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)


def run():

    options = {
            "bind": "%s:%s" % (args.host, args.port),
            "workers": args.workers if args.workers == 1 else ((multiprocessing.cpu_count() * 2) + 1),
            "worker_class": "uvicorn.workers.UvicornWorker",
        }
    StandaloneApplication("config.asgi:application", options).run()

if __name__ == "__main__":
    os.system("python manage.py migrate")
    run()