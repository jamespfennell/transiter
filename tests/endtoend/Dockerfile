FROM golang:1.25

WORKDIR /endtoend
COPY . .
CMD ["go", "test", "./tests/endtoend/...", "-v"]
