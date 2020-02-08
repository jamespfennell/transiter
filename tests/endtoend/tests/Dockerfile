FROM python:3.7

RUN pip install requests==2.22.0 gtfs-realtime-bindings==0.0.6 pytest==5.3.5

WORKDIR tests

COPY . .

ENTRYPOINT ["pytest", "."]

