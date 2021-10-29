#!/bin/bash

export OSS_ENDPOINT="10.52.21.125:10000"
export OSS_BUCKET="imu-auto-src"
export OSS_ACCESSKEY="RootAccessKey"
export OSS_SECRETKEY="JEYzvyMqr8kM2nMy"
# export PROCESSOR_APIHOST="http://localhost:8080/run"

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
               tcpbroker
else
    python main.py --port=$PORT
fi
