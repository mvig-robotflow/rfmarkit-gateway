# Note of credentials

## MinIO delopyment

```json
{
    "username": "admin",
    "password": "DePEbd@viwfUNA7zB"
}
```

### Critical resources

`/home/liyutong/Data/IMU/`

### Setup script

```bash
export BASE_DIR=/home/liyutong/Data/IMU
export CUSTOM_ROOT_USER=admin
export CUSTOM_ROOT_PASSWORD=DePEbd@viwfUNA7zB
export PATH_TO_DATA=$BASE_DIR/minio/data
export PATH_TO_CONFIG=$BASE_DIR/minio/config

mkdir -p $PATH_TO_DATA
mkdir -p $PATH_TO_CONFIG

useradd -u 1001 minio
sudo chown -R minio $BASE_DIR
sudo chgrp -R minio $BASE_DIR

sudo usermod -aG minio $USER

docker run \
    --restart=always \
    --user 1001 \
    --name minio \
    -p 10000:9000 \
    -p 10001:9001 \
    -d \
    -v $PATH_TO_DATA:/data \
    -v $PATH_TO_CONFIG:/root/.minio \
    -e "MINIO_ROOT_USER=$CUSTOM_ROOT_USER" \
    -e "MINIO_ROOT_PASSWORD=$CUSTOM_ROOT_PASSWORD" \
    bitnami/minio:2021
```

### AccessKey used for project

```json
{
    "access_key": "RootAccessKey",
    "secret_key": "JEYzvyMqr8kM2nMy"
}
```

## Docker

### Cross platform build

```bash
docker buildx build . --platform linux/amd64 -t <tag> --load
```

For instance:

```bash
docker buildx build . --platform linux/amd64 -t tcpbroker --load
```

### Docker run tcpbroker

#### OpenWhisk

image: `tcpbroker`

```bash
docker run -it \
           --rm \
           -p 18888:18888 \
           -e OSS_ENDPOINT="10.52.21.125:10000" \
           -e OSS_BUCKET="imu-test" \
           -e OSS_ACCESSKEY="RootAccessKey" \
           -e OSS_SECRETKEY="JEYzvyMqr8kM2nMy" \
           -e PROCESSOR_APIHOST="http://localhost:8080/run" \
           tcpbroker
```

#### Automated

```bash
docker run -it \
           --rm \
           -p 18888:18888 \
           -e OSS_ENDPOINT="10.52.21.125:10000" \
           -e OSS_BUCKET="imu-auto-src" \
           -e OSS_ACCESSKEY="RootAccessKey" \
           -e OSS_SECRETKEY="JEYzvyMqr8kM2nMy" \
           -e PROCESSOR_APIHOST="http://localhost:8080/run" \
           tcpbroker
```

### Docker run proc_mem

image: `procmem`

```bash
docker run -it \
           --rm \
           -e OSS_ENDPOINT="10.52.21.125:10000" \
           -e OSS_BUCKET="imu-test" \
           -e OSS_ACCESSKEY="RootAccessKey" \
           -e OSS_SECRETKEY="JEYzvyMqr8kM2nMy" \
           procmem
```

### Docker run proc_mem_auto

**preferred**

image: `procmemauto`

```bash
docker run -itd \
           --rm \
           -e OSS_ENDPOINT="10.52.21.125:10000" \
           -e OSS_SRC_BUCKET="imu-auto-src" \
           -e OSS_DST_BUCKET="imu-auto-dst" \
           -e OSS_ACCESSKEY="RootAccessKey" \
           -e OSS_SECRETKEY="JEYzvyMqr8kM2nMy" \
           procmemauto
```

### Python38dev

```bash
docker run -p 10022:22 -itd --name dev python38dev bash
```



## TODO
 
- 本地NTP服务器