FROM python:3.10

WORKDIR /endtoend

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py ./

ENTRYPOINT ["pytest", "-n", "8"]
