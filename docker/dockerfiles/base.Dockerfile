FROM python:3.7

MAINTAINER James Fennell jamespfennell@gmail.com

WORKDIR /transiter/source

# First install the dependencies. Doing this separately to installing
# the actual package gives us faster Docker builds when just the files
# in the package have changed.
COPY setup.py setup.py
COPY transiter/__version__.py transiter/__version__.py
RUN python setup.py egg_info
RUN pip install -r *.egg-info/requires.txt

# Then build the Transiter image.
COPY transiter transiter
RUN python setup.py sdist --dist-dir ../dist bdist_wheel --dist-dir ../dist

WORKDIR /transiter
RUN pip install dist/*whl

# The base image is never intended to used directly.
# This command is convenient for debugging.
CMD ["/bin/bash"]
