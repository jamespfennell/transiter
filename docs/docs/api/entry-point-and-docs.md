# Entry point and docs



## HTTP API entry point

`GET /`


Provides basic information about this Transiter instance and the Transit
systems it contains.

## Internal documentation

`GET /docs/<path:path>`


If internal documentation is enabled, this endpoint returns the requested
documentation HTML page.
The internal documentation system is described in a
[dedicated documentation page](../deployment/documentation.md).

If internal documentation is disabled, this endpoint always returns a 404 error -
i.e., Transiter behaves as if this endpoint doesn't exist.

Return code | Description
------------|-------------
`200 OK` | Internal documentation is enabled and the relevant page does not exist.
`404 NOT FOUND` | Internal documentation is disabled, or it is enabled and the requested page does not exist.
`503 SERVICE UNAVAILABLE` | Internal documentation is enabled but mis-configured. See the documentation page and the logs for debugging help.
