# This is the continuous integration Dockerfile. The resulting
# image is used, on Travis, to run the Python tests, build the
# documentation and distribute the Python package. It enables
# developers to fully replicate the CI environment locally.
#
# This image imports the Transiter base image using, essentially,
# composition instead of inheritence. The main consideration is
# avoiding a costly pip install of the developer requirements
# every time the base image is changed. Therefore, we instead copy
# over relevent files from the base image after those dev requirements
# have been installed.

FROM jamespfennell/transiter:latest-base AS transiter-base

FROM python:3.7

# We intentionally work in a separate directory to the source and
# distribution to avoid any cross-contamination.
WORKDIR /transiter-ci
COPY dev-requirements.txt dev-requirements.txt
RUN pip install -r dev-requirements.txt

# Bring in the base image using composition.
# The site-packages directory is determined using `python -m site`.
COPY --from=transiter-base /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages/
COPY --from=transiter-base /transiter /transiter

COPY docker/wait-for-it.sh docker/wait-for-it.sh
COPY .coveragerc .coveragerc
RUN mkdir coverage
COPY Makefile Makefile
COPY docs docs
COPY tests tests

ENTRYPOINT ["make"]

CMD ["-s", "nothing"]
