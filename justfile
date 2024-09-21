alias g := generate
alias t := test

# Print the list of recipes
default:
	just --list

# Build the Transiter binary and stamp it with the provided version
build VERSION="":
	go build --ldflags "-X github.com/jamespfennell/transiter/internal/version.version={{VERSION}}" .

# Build the Transiter Docker image
build-docker: _require-docker
	docker build . -t jamespfennell/transiter:latest

# Build the Transiter documentation
docs OUTPUT_DIR="docs/gen":
	pip install -r docs/requirements.txt
	mkdocs build --strict -f docs/mkdocs.yml -d ../{{OUTPUT_DIR}}

# Preview the Transiter documentation on 0.0.0.0:8001
docs-preview: docs
	python3 -m http.server 8001 -d docs/gen

# Run the CI steps. Requires Docker and Postgres. Assumes the Docker image has already been built.
ci: test _run_e2e lint

# Run code autoformatters
fmt:
	go fmt ./...
	buf format -w

# Generate the DB and proto API code
generate:
	sqlc --experimental generate
	buf generate
	go run docs/src/api/api_docs_gen.go

# Install all tools for working on Transiter
install-tools: install-linters
	go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@v2.15.2
	go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.30.0
	go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.1.0
	go install github.com/pseudomuto/protoc-gen-doc/cmd/protoc-gen-doc@v1.5.1
	go install github.com/kyleconroy/sqlc/cmd/sqlc@v1.17.2
	go install github.com/bufbuild/buf/cmd/buf@v1.13.1

# Install linters used on Transiter
install-linters:
	go install honnef.co/go/tools/cmd/staticcheck@2023.1

# Print the versions of all tools
tool-versions:
	protoc --version
	protoc-gen-go --version
	protoc-gen-grpc-gateway --version
	protoc-gen-go-grpc --version
	protoc-gen-doc --version
	sqlc version
	buf --version
	staticcheck --version

# Run all the linters
lint: install-linters
	staticcheck ./...

# Run all the unit tests
test:
	go test ./...
# Run all the E2E tests (requires Docker)
test-e2e: build-docker _run_e2e
# Run all the unit and E2E tests (requires Docker)
test-all: test test-e2e

_require-docker:
	@echo "Checking that Docker and Docker compose are installed. These tools are required for this recipe."
	which docker

_run_e2e: _require-docker
	#!/usr/bin/env sh
	docker compose -f tests/endtoend/compose.yml down
	docker compose -f tests/endtoend/compose.yml up --build --detach sourceserver transiter db
	docker compose -f tests/endtoend/compose.yml up --build --exit-code-from testrunner testrunner  || RESULT=$?
	docker compose -f tests/endtoend/compose.yml down
	exit ${RESULT}
