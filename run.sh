docker run -p 18888:18888 \
           -p 5051:5051 \
           -v "$(pwd)"/imu_data:/opt/app/imu_data \
           --rm \
           tcpbroker
