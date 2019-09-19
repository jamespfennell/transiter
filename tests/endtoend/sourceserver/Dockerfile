FROM python:3.7

RUN pip install flask

WORKDIR sourceserver

COPY main.py main.py

ENV SOURCE_SERVER_PORT 5001

EXPOSE 5001

ENTRYPOINT ["python", "main.py"]
