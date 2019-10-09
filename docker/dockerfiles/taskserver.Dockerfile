FROM jamespfennell/transiter:latest-base

ENV TRANSITER_TASKSERVER_HOST 0.0.0.0
ENV TRANSITER_TASKSERVER_PORT 18812

EXPOSE 18812

ENTRYPOINT ["transiterclt", "launch", "task-server"]
