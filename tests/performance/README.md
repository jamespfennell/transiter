# Transiter performance tool

This is a Go application that measures the performance
of a Transiter application. 
It concurrently runs many Transiter clients who
navigate the REST API. 
The response times for the main endpoints are measured
and printed.

By default, the tool tests `demotransiter.dev` and can be run
using `go run main.go`.
To see the available configurations run `go run main.go --help`.

Because Transiter is a Python application it would have been
most ideal to write the tool in Python.
However, the main thing the tool needs to do is run many
clients concurrently and doing this in Go 
is an order of magnitude easier.

