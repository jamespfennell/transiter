FROM python:3.10

WORKDIR /endtoend

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY data data
COPY *.py ./
RUN rm test_feedflush.py

ENTRYPOINT ["pytest", "-n", "4"]
