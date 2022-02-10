FROM python:3.8.0

ENV LANG=C.UTF-8

WORKDIR /opt/app/

COPY ["requirements.txt", "/opt/app/" ]

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt

COPY ["config.py", "main.py", "/opt/app/" ]
COPY /tasks/ /opt/app/tasks/
COPY /applications/ /opt/app/applications/


ENTRYPOINT ["python"]
EXPOSE 18888

CMD ["main.py"]
