import multiprocessing
import os

bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_connections = 1000
timeout = 120
keepalive = 5
backlog = 2048

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

max_requests = 1000
max_requests_jitter = 50

preload_app = False
reload = False

def when_ready(server):
    server.log.info(f"Gunicorn ready with {workers} workers")

def worker_int(worker):
    worker.log.info(f"Worker {worker.pid} received INT signal")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    pass
