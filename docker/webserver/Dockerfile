FROM python:3.7

MAINTAINER James Fennell jamespfennell@gmail.com

COPY transiter /transiter/transiter
COPY setup.py /transiter/setup.py

RUN pip install /transiter


RUN pip install gunicorn

EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "transiter.http:wsgi_app"]
