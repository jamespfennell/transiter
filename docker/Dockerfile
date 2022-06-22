FROM python:3.9 AS transiter-documentation-builder

WORKDIR /transiter-docs

COPY docs/requirements.txt .
RUN pip install --quiet -r requirements.txt

COPY docs ./
RUN mkdocs build

FROM python:3.9

WORKDIR /transiter/source

# First install the dependencies. Doing this separately to installing
# the actual package gives us faster Docker builds when just the files
# in the package have changed.
COPY setup.py setup.py
COPY README.md README.md
COPY transiter/__metadata__.py transiter/__metadata__.py
RUN python setup.py --quiet egg_info
RUN pip install --quiet -r *.egg-info/requires.txt

COPY --from=transiter-documentation-builder /transiter-docs/site /transiter-docs
ENV TRANSITER_DOCUMENTATION_ROOT /transiter-docs

# Then build the Transiter image.
COPY transiter transiter
RUN python setup.py --quiet sdist --dist-dir ../dist bdist_wheel --dist-dir ../dist

WORKDIR /transiter
RUN pip install --quiet dist/*whl

# The base image is never intended to used directly.
# This command is convenient for debugging.
CMD ["/bin/bash"]
