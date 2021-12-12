FROM python:3.9

WORKDIR /sourceserver

RUN pip install flask==2.0.2 gunicorn==20.1.0

COPY sourceserver.py .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8090", "-w", "1", "sourceserver:app"]
