#!/bin/sh
python -u -m gunicorn --worker-class eventlet -w 1 application:app -b 0.0.0.0:7010
