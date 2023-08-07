FROM golang:1.19 AS builder

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
RUN curl -sSL "https://github.com/bufbuild/buf/releases/download/v1.13.1/buf-$(uname -s)-$(uname -m)" \
    -o "/usr/bin/buf"
RUN chmod +x "/usr/bin/buf"

# Generate the gRPC files
COPY buf.gen.yaml .
COPY buf.lock .
COPY buf.yaml .
COPY api api
RUN buf generate

# Generate the DB files
COPY sqlc.yaml .
COPY db db
RUN sqlc --experimental generate

# Move the newly generated files so that they don't get clobbered when we copy the source code in
RUN mv internal/gen internal/genNew

COPY . ./

# Diff the newly generated files with the ones in source control.
# If there are differences, this will fail
RUN diff --recursive internal/gen internal/genNew
RUN rm -r internal/genNew

ARG TRANSITER_VERSION
RUN go build --ldflags "-X github.com/jamespfennell/transiter/internal/version.version=${TRANSITER_VERSION}"  .

# Only build the image if the tests pass
RUN SKIP_DATABASE_TESTS=true go test ./...

# We use this buildpack image because it already has SSL certificates installed
FROM buildpack-deps:buster-curl
COPY --from=builder /transiter/transiter /usr/bin
ENTRYPOINT ["transiter"]
