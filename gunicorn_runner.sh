#!/bin/sh
gunicorn --bind 0.0.0.0:8002 core.docker_wsgi -c gunicorn_docker.py