#!/bin/bash

PORT=18888

if [[ $# -ge 1 && $1 = "docker" ]]; then
    echo "Run Docker"
    docker run -it \
               --rm \
               -p $PORT:18888 \
               -e OSS_ENDPOINT=$OSS_ENDPOINT \
               -e OSS_BUCKET=$OSS_BUCKET \
               -e OSS_ACCESSKEY=$OSS_ACCESSKEY \
               -e OSS_SECRETKEY=$OSS_SECRETKEY \
               -e PROCESSOR_APIHOST=$PROCESSOR_APIHOST \
               -v ./imu_data:/opt/app/imu_data \
               tcpbroker
else
    python main.py --port=$PORT
fi
