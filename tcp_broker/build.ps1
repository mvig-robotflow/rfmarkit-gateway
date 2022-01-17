echo "Building tcpbroker"
docker build -t tcpbroker .

# Free dangling images
docker image prune -f