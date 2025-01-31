FROM golang:1.22

WORKDIR /endtoend
COPY . .
CMD ["go", "test", "./tests/endtoend/...", "-v"]
