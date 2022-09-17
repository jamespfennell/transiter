# Transiter APIs

This directory contains the definitions of the two Transiter APIs:

- The _public API_ provides read-only views of the transit data
  in a Transiter instance.
  It is designed to be accesible from the internet (e.g. via
  a reverse proxy) and is the basis for building apps on top
  of Transiter.

- The _admin API_ provides methods for managing a Transiter instance;
  e.g., installing and deleting transit systems and manually performing feed
  updates.
  It is dangerous to have this API accesible to the internet because
  anyone could delete all of the transit system installed.
  A simple approach for this API is to have it listening on some
  local port on the machine running Transiter, and then interacting
  with it using client commands on that machine, or on another machine
  after SSH port forwarding has been set up.

The API schemas are defined using protobuf/gRPC.
However the Transiter APIs are designed primary to be HTTP/JSON/REST APIs.
The protobuf/gRPC format is used because it provides many conveniences,
  such as strong typing
  and autogeneration of server and client code.
Having the option of using gRPC is also nice,
  and this is what is used in the Transiter CLI.

Given a protobuf/gRPC definition of an endpoint, the HTTP
semantics can be figured out by looking at the Google HTTP
annotations.
For example, this is the list agencies endpoint:
```
rpc ListAgencies(ListAgenciesRequest) returns (ListAgenciesReply) {
  option (google.api.http) = {
    get: "/systems/{system_id}/agencies"
  };
}
```
We can see that it uses the HTTP GET verb with the provided URL.
The request type `ListAgenciesRequest` contains at least the field `system_id`.
Any other fields in the request type (such as `filter_by_id`)
are passed as URL parameters:
```
curl $TRANSITER_URL/systems/us-ny-subway/agencies?filter_by_id=true&id=MTA
```
The response type is provided as JSON.
The protobuf fields are named using snake case,
  but the JSON response uses camel case.

The documentation in the proto files
  can be read in a more friendly format
  on [the Transiter documentation website](https://docs.transiter.dev).
