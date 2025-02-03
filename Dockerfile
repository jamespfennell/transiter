# (A) Build the Go binary
FROM golang:1.22 AS builder
WORKDIR /transiter

# (1) Install all the dependencies before copying in the source code.
# This ensures that if we change the Go source code we don't have to redo all of
# these (slow) steps again when building the Docker image, due to Docker's 
# incremental caching.
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "/usr/bin"
COPY go.mod ./
COPY go.sum ./
RUN go mod download
COPY justfile ./

# (2) Next, we perform an optional step in which we re-generate all of the sqlc and
# proto code and validate that it matches what's in source control.
# The idea is to make sure the repo is internally consistent and that the Docker image
# we're building actually reflects what's in the .proto and .sql files.

# (2.1) Install all the code generation tools.
RUN just install-tools

# (2.2) Generate the gRPC and DB files.
COPY buf.gen.yaml .
COPY buf.lock .
COPY buf.yaml .
COPY api api
COPY sqlc.yaml .
COPY db db
COPY docs/src/api/api_docs_gen.go docs/src/api/api_docs_gen.go
RUN just generate

# (2.3) Move the newly generated files so that they don't get clobbered when we copy the source code in.
# Then copy the source in.
RUN mv internal/gen internal/genNew
RUN mv docs/src/api docs/src/apiNew
RUN rm docs/src/apiNew/api_docs_gen_input.json
COPY . ./

# (2.4) Diff the newly generated files with the ones in source control.
# If there are differences, this will fail
RUN diff --recursive internal/gen internal/genNew
RUN rm -r internal/genNew
RUN diff --recursive docs/src/api docs/src/apiNew
RUN rm -r docs/src/apiNew

# (3) Build the binary.
ARG TRANSITER_VERSION
RUN just build ${TRANSITER_VERSION}


# (B) Build the documentation
FROM python:3.9 AS docs-builder
WORKDIR /transiter
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "/usr/bin"
COPY justfile ./
COPY docs/requirements.txt docs/
RUN pip install -r docs/requirements.txt
COPY docs/mkdocs.yml docs/
COPY docs/src docs/src
RUN just docs


# (C) Pull in the Caddy binary as a dependency
FROM caddy:2 AS caddy


# (D) Put it all together.
# We use this buildpack image because it already has SSL certificates installed
FROM buildpack-deps:bookworm-curl
COPY --from=caddy /usr/bin/caddy /usr/bin
COPY --from=docs-builder /transiter/docs/gen /usr/share/doc/transiter
COPY --from=builder /transiter/transiter /usr/bin
ENTRYPOINT ["transiter"]
 
