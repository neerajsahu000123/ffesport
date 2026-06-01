# Gunicorn production config
import os
workers     = int(os.environ.get('WEB_CONCURRENCY', 2))
threads     = 4
worker_class= 'gthread'
bind        = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
timeout     = 60
keepalive   = 5
loglevel    = 'info'
accesslog   = '-'
errorlog    = '-'
preload_app = True
