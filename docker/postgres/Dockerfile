
FROM python:3.7 AS transiter-schema-builder

COPY transiter /transiter/transiter
COPY setup.py /transiter/setup.py

RUN pip install /transiter

RUN mkdir -p /schema
RUN transiterclt generate-schema > /schema/transiter.sql



FROM postgres

ENV POSTGRES_USER transiter
ENV POSTGRES_PASSWORD transiter
ENV POSTGRES_DB transiter

COPY --from=transiter-schema-builder /schema/transiter.sql /docker-entrypoint-initdb.d/transiter.sql

