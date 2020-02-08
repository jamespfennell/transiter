FROM python:3.7

RUN pip install Flask==1.1.1

WORKDIR sourceserver

COPY new.py new.py

EXPOSE 5001

ENTRYPOINT ["python", "new.py"]
