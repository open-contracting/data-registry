#!/bin/sh
gunicorn --bind 0.0.0.0:8002 core.amy01_wsgi -c gunicorn_amy01.py