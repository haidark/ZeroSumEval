#!/bin/bash
set -ex

docker build -t quack .
docker run --pids-limit 100 --read-only -d -p 9999:22 quack