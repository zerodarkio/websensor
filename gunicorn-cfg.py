import gunicorn

max_requests = 1000
max_requests_jitter = 50

bind = '0.0.0.0:8000'
workers = 1
accesslog = '-'
loglevel = 'debug'
capture_output = True
copy_env = true
enable_stdio_inheritance = True
