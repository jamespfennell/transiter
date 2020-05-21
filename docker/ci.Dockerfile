# This is the continuous integration Dockerfile. The resulting
# image is used, on Travis, to run the Python tests, build the
# documentation and distribute the Python package. It enables
# developers to fully replicate the CI environment locally.


FROM jamespfennell/transiter:latest

# We intentionally work in a separate directory to the source and
# distribution to avoid any cross-contamination.
WORKDIR /transiter-ci
COPY dev-requirements.txt dev-requirements.txt
RUN pip install --quiet -r dev-requirements.txt

COPY Makefile Makefile
COPY docs docs
COPY tests tests

ENTRYPOINT ["make"]

CMD ["-s", "nothing"]
