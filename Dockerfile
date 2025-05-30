# syntax=docker/dockerfile:1

# (A) Prepare base & build the Go binary
# Use the builder platform to cross-compile to the target platform.
FROM --platform=${BUILDPLATFORM} golang:1.22-bookworm AS builder
WORKDIR /transiter

RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "/usr/bin"

FROM builder AS codegen

# (2) Next, we perform an optional step in which we re-generate all of the sqlc and
# proto code and validate that it matches what's in source control.
# The idea is to make sure the repo is internally consistent and that the Docker image
# we're building actually reflects what's in the .proto and .sql files.

# (2.1) Install all the code generation tools.
COPY justfile .
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    just install-tools

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

FROM builder AS build

# (3) Build the binary.
# As soon as TARGETOS/TARGETARCH are defined, the build will differ
# for each target platform during cross-compilation.
ARG TRANSITER_VERSION
ARG TARGETOS
ARG TARGETARCH
ENV GOOS=${TARGETOS}
ENV GOARCH=${TARGETARCH}
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    --mount=type=bind,source=.,target=/transiter \
    EXTRA_LDFLAGS='-w' EXTRA_GOFLAGS='-trimpath -o /out/transiter' \
    just build ${TRANSITER_VERSION}

# (B) Build the documentation
# This is not platform-dependendent, so can be done once on the native
# build platform and shared by all target platforms.
FROM --platform=${BUILDPLATFORM} python:3.9 AS docs-builder
WORKDIR /transiter
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "/usr/bin"
COPY justfile ./
COPY docs/requirements.txt docs/
RUN pip install -r docs/requirements.txt
COPY docs/mkdocs.yml docs/
COPY docs/src docs/src
RUN just docs


# (C) Pull in the Caddy binary as a dependency (for the target platform).
FROM caddy:2 AS caddy


# (D) Put it all together.
# We use this buildpack image because it already has SSL certificates installed
# No emulation is required because there are no RUN statements.
FROM buildpack-deps:bookworm-curl
COPY --link --from=caddy /usr/bin/caddy /usr/bin/
COPY --link --from=docs-builder /transiter/docs/gen /usr/share/doc/transiter
COPY --link --from=build /out/transiter /usr/bin/
ENTRYPOINT ["transiter"]
