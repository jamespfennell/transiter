FROM python:3.7

RUN apt-get update
RUN apt-get install zip

RUN pip install requests gtfs-realtime-bindings
WORKDIR runner


COPY data data

RUN zip -jr data/gtfsstaticdata.zip data/gtfsstatic/*

COPY runner runner

# ENTRYPOINT ["python", "test_one.py"]

ENTRYPOINT ["python", "-m", "unittest", "discover", "."]
