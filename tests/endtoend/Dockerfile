FROM python:3.9

WORKDIR /tests

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY data data
COPY conftest.py .
COPY __init__.py .
COPY gtfsrealtimegenerator.py .
COPY test_installsystem.py .
COPY test_servicemaps.py .
COPY test_trips.py .

ENTRYPOINT ["pytest"]
