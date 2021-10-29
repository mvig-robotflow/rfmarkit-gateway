#!/bin/bash

set -e

CURR_DIR=$(pwd)

echo "Building procmem"
docker build -f $CURR_DIR/docker/proc_mem/Dockerfile -t procmem .

echo "Building procmem_auto"
docker build -f $CURR_DIR/docker/proc_mem_auto/Dockerfile -t procmemauto .

# Free dangling images
docker image prune -f