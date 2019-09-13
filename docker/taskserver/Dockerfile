FROM python:3.7

MAINTAINER James Fennell jamespfennell@gmail.com

COPY transiter /transiter/transiter
COPY setup.py /transiter/setup.py

RUN pip install /transiter



ENTRYPOINT ["transiterclt", "launch", "task-server"]

