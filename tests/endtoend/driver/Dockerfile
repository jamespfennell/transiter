FROM python:3.7

RUN apt-get update
RUN apt-get install zip

RUN pip install requests gtfs-realtime-bindings
WORKDIR runner

ENV TRANSITER_URL http://webserver:80
ENV SOURCE_SERVER_URL http://sourceserver:5001

COPY data data

RUN zip -jr data/gtfsstaticdata.zip data/gtfsstatic/*

COPY driver driver

ENTRYPOINT ["python", "-m", "unittest", "discover", "."]
