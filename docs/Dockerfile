FROM golang:1.19 AS api-docs-builder

WORKDIR /transiter

COPY go.mod ./
COPY go.sum ./
RUN go mod download

# Install all the code generation tools.
RUN go install \
    github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway \
    github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2 \
    google.golang.org/protobuf/cmd/protoc-gen-go \
    google.golang.org/grpc/cmd/protoc-gen-go-grpc \
    github.com/pseudomuto/protoc-gen-doc/cmd/protoc-gen-doc \
    github.com/kyleconroy/sqlc/cmd/sqlc
RUN curl -sSL "https://github.com/bufbuild/buf/releases/download/v1.6.0/buf-$(uname -s)-$(uname -m)" \
    -o "/usr/bin/buf"
RUN chmod +x "/usr/bin/buf"

# Generate the gRPC files
COPY buf.gen.yaml .
COPY buf.lock .
COPY buf.yaml .
COPY api api
RUN buf generate

# At this point the Dockerfile diverges from the main Dockerfile

COPY docs/src/api/api_docs_gen.go docs/src/api/api_docs_gen.go
RUN go run docs/src/api/api_docs_gen.go


FROM python:3.9 AS docs-builder
WORKDIR /transiter

COPY docs/requirements.txt .
RUN pip install -r requirements.txt

COPY docs/mkdocs.yml .
COPY docs/src src

# Diff the newly generated files with the ones in source control.
# If there are differences, this will fail
COPY --from=api-docs-builder /transiter/docs/src/api/*md /tmp/apiGenFresh/
RUN rm src/api/api_docs_gen*
RUN diff --recursive /tmp/apiGenFresh src/api

RUN ls -lah
RUN mkdocs build --strict -f mkdocs.yml -d gen

FROM caddy:2
WORKDIR /transiter
COPY --from=docs-builder /transiter/gen .
ENTRYPOINT ["caddy", "file-server", "--listen", ":80"]
