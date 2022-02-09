#!/bin/zsh
set -e

echo "Building tcpbroker"
docker build -t tcpbroker .

# Free dangling images
docker image prune -f