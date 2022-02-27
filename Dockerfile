FROM python:3.8.0

ENV LANG=C.UTF-8

WORKDIR /opt/app/

COPY ["requirements.txt", "/opt/app/" ]

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt

COPY [ "config.json", "/opt/app/" ]
COPY tcpbroker/tcpbroker /opt/app/
COPY cvt_measurement/cvt_measurement /opt/app/

ENTRYPOINT ["python"]

EXPOSE 18888 5050

CMD [" tcpbroker.main -p"]
