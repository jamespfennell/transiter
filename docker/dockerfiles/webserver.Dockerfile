FROM jamespfennell/transiter:latest-base

RUN pip install gunicorn

EXPOSE 80

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:80", "transiter.http:wsgi_app"]
