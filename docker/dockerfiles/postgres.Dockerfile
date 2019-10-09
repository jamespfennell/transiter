FROM jamespfennell/transiter:latest-base AS transiter-schema-builder

WORKDIR /transiter-schema
RUN transiterclt generate-schema > transiter.sql

FROM postgres

ENV POSTGRES_USER transiter
ENV POSTGRES_PASSWORD transiter
ENV POSTGRES_DB transiter

COPY --from=transiter-schema-builder /transiter-schema/transiter.sql /docker-entrypoint-initdb.d/transiter.sql

