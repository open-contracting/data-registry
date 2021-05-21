#!/bin/sh
docker build -t data-registry:production .
aws ecr get-login-password --region eu-central-1 --profile datlab | docker login --username AWS --password-stdin 170654793963.dkr.ecr.eu-central-1.amazonaws.com
docker tag data-registry:production 170654793963.dkr.ecr.eu-central-1.amazonaws.com/data-registry:production
docker push 170654793963.dkr.ecr.eu-central-1.amazonaws.com/data-registry:production