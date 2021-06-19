#!/bin/sh
gunicorn --bind 0.0.0.0:$1 core.docker_wsgi -c gunicorn_docker.py