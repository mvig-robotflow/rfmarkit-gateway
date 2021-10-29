#!/bin/bash

export OSS_ENDPOINT="10.52.21.125:10000"
export OSS_SRC_BUCKET="imu-auto-src"
export OSS_DST_BUCKET="imu-auto-dst"
export OSS_ACCESSKEY="RootAccessKey"
export OSS_SECRETKEY="JEYzvyMqr8kM2nMy"

docker run -itd \
           --rm \
           --name procmemautod \
           -e OSS_ENDPOINT=$OSS_ENDPOINT \
           -e OSS_SRC_BUCKET=$OSS_SRC_BUCKET \
           -e OSS_DST_BUCKET=$OSS_DST_BUCKET \
           -e OSS_ACCESSKEY=$OSS_ACCESSKEY \
           -e OSS_SECRETKEY=$OSS_SECRETKEY \
           procmemauto