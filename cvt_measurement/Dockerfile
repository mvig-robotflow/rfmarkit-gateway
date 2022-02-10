FROM python:3.8.0

ENV LANG=C.UTF-8

WORKDIR /opt/app/

COPY ["requirements.txt", "/opt/app/" ]

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt

COPY [ "cvt_measurement.py", "imu_parser.py", "digest.py", "/opt/app/" ]

ENTRYPOINT ["python"]
EXPOSE 18880

CMD ["digest.py"]
