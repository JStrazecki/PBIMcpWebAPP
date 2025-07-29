# Gunicorn configuration for Azure App Service
bind = "0.0.0.0:8000"
workers = 1
timeout = 600
accesslog = "-"
errorlog = "-"
loglevel = "info"