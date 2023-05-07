FROM python:3.10

WORKDIR /tests

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY data data
COPY conftest.py .
COPY __init__.py .
COPY gtfs_realtime_pb2.py .
COPY gtfsrealtimegenerator.py .
COPY test_alerts.py .
COPY test_installsystem.py .
COPY test_periodicupdate.py .
COPY test_servicemaps.py .
COPY test_trips.py .
COPY test_vehicles.py .

ENTRYPOINT ["pytest", "-n", "4"]
