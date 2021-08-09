#!/bin/sh
gunicorn --bind 0.0.0.0:$1 core.docker_wsgi --timeout 720 -c gunicorn_docker.py