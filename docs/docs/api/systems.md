# Systems


Endpoints for installing, reading, configuring and deleting transit systems.

## List all systems

`GET /systems`


List all transit systems that are installed in this Transiter instance.

## Get a specific system

`GET /systems/<system_id>`


Get a system by its ID.

Return code | Description
------------|-------------
`200 OK` | A system with this ID exists.
`404 NOT FOUND` | No system with the provided ID is installed.

## List all transfers in a system

`GET /systems/<system_id>/transfers`


List all transfers in a system.

Return code | Description
------------|-------------
`200 OK` | A system with this ID exists.
`404 NOT FOUND` | No system with the provided ID is installed.

## Install a system

`PUT /systems/<system_id>`


This endpoint is used to install or update transit systems.
Installs/updates can be performed asynchronously (recommended)
or synchronously (using the optional URL parameter `sync=true`; not recommended);
see below for more information.

The endpoint accepts `multipart/form-data` requests.
There is a single required parameter, `config_file`, which
specifies the YAML configuration file for the Transit system.
(There is a [dedicated documentation page](systems.md) concerned with creating transit system configuration files.)
The parameter can either be:

- A file upload of the configuration file, or
- A text string, which will be interpreted as a URL pointing to the configuration file.

In addition, depending on the configuration file, the endpoint will also accept extra text form data parameters.
These additional parameters are used for things like API keys, which are different
for each user installing the transit system.
The configuration file will customize certain information using the parameters -
    for example, it might include an API key as a GET parameter in a feed URL.
If you are installing a system using a YAML configuration provided by someone else, you
 should be advised of which additional parameters are needed.
If you attempt to install a system without the required parameters, the install will fail and
the response will detail which parameters you're missing.

#### Async versus sync

Often the install/update process is long because it often involves performing
large feed updates
of static feeds - for example, in the case of the New York City Subway,
an install takes close to two minutes.
If you perform a synchronous install, the install request is liable
to timeout - for example, Gunicorn by default terminates HTTP
requests that take over 60 seconds.
For this reason you should generally install asynchronously.

After triggering the install asynchronously, you can track its
progress by hitting the `GET` system endpoint repeatedly.

Synchronous installs are supported and useful when writing new
transit system configs, in which case getting feedback from a single request
is quicker.

Return code         | Description
--------------------|-------------
`201 CREATED`       | For synchronous installs, returned if the transit system was successfully installed.
`202 ACCEPTED`      | For asynchronous installs, returned if the install is successfully triggered. This does not necessarily mean the system will be succesfully installed.
`400 BAD REQUEST`   | Returned if the YAML configuration file cannot be retrieved. For synchronous installs, this code is also returned if there is any kind of install error.

## Uninstall (delete) a system

`DELETE /systems/<system_id>`


The uninstall can be performed asynchronously or synchronously (using the
optional URL parameter `sync=true`).

You should almost always use the asynchronous version of this endpoint.
It works by changing the system ID to be a new "random" ID, and then performs
the delete asynchronously.
This means that at soon as the HTTP request ends (within a few milliseconds)
the system is invisible to users, and available for installing a new system.

The actual delete takes up to a few minutes for large transit systems like
the NYC Subway.

Return code         | Description
--------------------|-------------
`202 ACCEPTED`      | For asynchronous deletes, returned if the delete is successfully triggered.
`204 NO CONTENT`    | For synchronous deletes, returned if the system was successfully deleted.
`404 NOT FOUND`     | Returned if the system does not exist.

## Configure system auto-update

`PUT /systems/<system_id>/auto-update`


Configure whether auto-update is enabled for
 auto-updatable feeds in a system.

The endpoint takes a single form parameter `enabled`
which can either be `true` or `false` (case insensitive).

Return code         | Description
--------------------|-------------
`204 NO CONTENT`    | The configuration was applied successfully.
`400 BAD REQUEST`   | Returned if the form parameter is not provided or is invalid.
`404 NOT FOUND`     | Returned if the system does not exist.
