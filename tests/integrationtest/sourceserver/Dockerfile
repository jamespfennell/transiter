FROM python:3.7

RUN pip install flask gunicorn

WORKDIR sourceserver

COPY main.py main.py

EXPOSE 8000

# TODO: just use flask instead. Gunicorn can spawn multiple workers :(
ENTRYPOINT ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "main:app"]
