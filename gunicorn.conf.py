# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = max(multiprocessing.cpu_count() * 2 + 1, 5)
worker_class = "gthread"
threads = 2
worker_tmp_dir = "/dev/shm"  # Use shared memory for worker heartbeat

# Timeouts
timeout = 60
keepalive = 5
graceful_timeout = 30

# Logging
errorlog = "-"  # stderr
accesslog = "-"  # stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "sync_option"

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
capture_output = True
enable_stdio_inheritance = True 