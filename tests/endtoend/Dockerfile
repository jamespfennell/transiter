FROM python:3.9

WORKDIR /tests

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY data data
COPY conftest.py .
COPY test_installsystem.py .

ENTRYPOINT ["pytest"]
