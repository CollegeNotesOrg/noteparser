"""
Gunicorn configuration for production deployment.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("WORKER_CLASS", "uvicorn.workers.UvicornWorker")
worker_connections = 1000
max_requests = int(os.getenv("MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", 100))
timeout = int(os.getenv("TIMEOUT", 300))
keepalive = 2

# Restart workers after this many seconds
max_worker_age = 3600

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "noteparser"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True

# Graceful shutdown
graceful_timeout = 30

# Monitoring
statsd_host = os.getenv("STATSD_HOST")
if statsd_host:
    statsd_prefix = "noteparser"

# Worker process hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting NoteParser server")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading NoteParser server")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Pre-fork worker {worker.pid}")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Post-fork worker {worker.pid}")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} aborted")

# Application-specific settings
def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    from noteparser.web.app import create_app
    
    # Initialize application-specific resources
    app = create_app()
    
    # Setup logging for the worker
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    worker.log.info(f"Worker {worker.pid} initialized with AI services")

# Environment-specific configurations
if os.getenv("NOTEPARSER_ENV") == "production":
    # Production-specific settings
    workers = max(2, multiprocessing.cpu_count())
    worker_class = "uvicorn.workers.UvicornWorker"
    preload_app = True
    
elif os.getenv("NOTEPARSER_ENV") == "development":
    # Development-specific settings
    workers = 1
    reload = True
    loglevel = "debug"