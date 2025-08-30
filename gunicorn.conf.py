# Gunicorn configuration file
# This file configures Gunicorn settings for production deployment

# Server socket
import os
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeout settings - Increased to handle long-running operations
timeout = 120  # Worker timeout in seconds (increased from default 30s)
keepalive = 5
graceful_timeout = 30

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "logisedge_gunicorn"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=logisEdge.settings',
]

# Restart workers after this many requests, with up to half that number
# of jitter added to the restart to avoid all workers restarting at the same time
max_requests = 1000
max_requests_jitter = 500

# The maximum number of pending connections
backlog = 2048

# Restart workers after this many seconds
max_worker_memory = 200  # MB
worker_tmp_dir = "/dev/shm"

# Preload application for better performance
preload_app = True

# Enable threading for better concurrency
threads = 2

# Worker timeout for handling requests
# This is the main setting to fix WORKER TIMEOUT errors
timeout = 120  # 2 minutes timeout

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Keep alive connections
keepalive = 5

# Enable access logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Capture output from workers
capture_output = True

# Enable stats
enable_stdio_inheritance = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190