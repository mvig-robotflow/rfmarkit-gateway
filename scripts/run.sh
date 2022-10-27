docker run -p 18888:18888 \
           -p 5051:5051 \
           --name tcpbroker \
           -v "$(pwd)"/imu_data:/opt/app/imu_data \
           -it \
           --rm \
           tcpbroker
