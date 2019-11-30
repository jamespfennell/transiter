# Deployment


## Container based deployments

The simplest way to deploy Transiter is to use
containers along with the included configurations
for either Kubernetes (using the Transiter Helm Chart) or Docker compose.

During Transiter's continuous integration process, three 
Docker images are built and uploaded to Docker hub: 

- `jamespfennell/transiter:<version>-webserver` -
    the Transiter web service for responding to HTTP requests through the API.
    This image uses Gunicorn for serving the WSGI app.
    In deployment you can run as many replicas of this image as you please.

- `jamespfennell/transiter:<version>-taskserver` -
    the process that performs automatic feed updates.
    This is a scheduling process and, as such, only one should be running at any time.
    
- `jamespfennell/transiter:<version>-postgres` -
    this is the standard Postgres Docker image with Transiter database schema pre-loaded.
    
Here `<version>` can be any of the following:

- For stable releases, this is the version number of the release; for example `0.3.1`.

- Setting `<version>` to be `latest` will spin up the most recent stable release.

- Setting `<version>` to be `dev-latest` will spin up the most recent green build on master.

For production settings, pinning to a fixed stable release is, of course, recommended.
The `latest` and `dev-latest` versions may introduce breaking API changes at any time.

### Kubernetes: the Transiter Helm Chart

(Coming soon)

### Docker compose

There is a [Docker compose configuration in the Github repository](https://raw.githubusercontent.com/jamespfennell/transiter/master/docker/docker-compose.yml)
that may be used a basis for a deployment.
Using Docker compose has its limitations in terms of customization.
The 
configuration file is mostly maintained to enable running a simpler CI pipeline on Travis,
rather than being a recommended deployment mode.

When launched, the Docker compose config starts a Transiter instance listening on port 8000.

In production, you should use a volume for the Postgres data directory to ensure
that data persists if the Postgres container is reset.
By default that Postgres data directory does *not* do this.
To enable a volume, change
```yaml
      - data-volume:/var/lib/postgresql/data-not-used
```
to
```yaml
      - data-volume:/var/lib/postgresql/data
```
and configure the volume `data-volume` appropriately.


## Running Transiter without containers


### Setting up Postgres

Postgres is the only officially supported database for Transiter right now.
Other systems such as SQLite and MySQL can be used with some tinkering and
 may be supported in the future;
start an issue on the issue tracker if you're interested.

By default, Transiter connects to Postgres using the following configuration.

Setting     | Default   | Environment variable to change the default
------------|-----------|---------------------------------
Host        | localhost | `TRANSITER_DB_HOST`
Port        | 5432      | `TRANSITER_DB_PORT`
Database    | transiter | `TRANSITER_DB_DATABASE`
Username    | transiter | `TRANSITER_DB_USERNAME`
Password    | transiter | `TRANSITER_DB_PASSWORD`

In order to change the default, set the environment variable
in any environment that a Transiter process (web service or task server)
will be running.

After setting up Postgres and a database, you need to 
initialize the database with the Transiter schema.
Assuming you're in a (virtual) environment in which the `transiter`
Python package has been installed, this can be done by running:
```sh
transiterclt rebuild-db
```

### Running the web service

The Transiter web service response to HTTP requests.
Transiter was built using the Flask framework and thus 
contains a WSGI app for launching a HTTP service.

Assuming you have the `transiter` Python package installed,
Transiter's WSGI app is located at `transiter.http:wsgi_app`
So, for example, to launch a Transiter web service using Gunicorn:
```sh
gunicorn transiter.http:wsgi_app
```

If you're developing Transiter
it can be helpful to launch the web service in debug mode so that it 
automatically restarts when you've made changes.
Assuming you're in a Python (virtual) environment in which Transiter has 
been installed, run:

```sh
transiterclt launch http-debug-server
```
This launches the Flask debugging server.


### Running the task server

The task server is responsible for performing periodic feed updates.
It can be launched using:
```sh
transiterclt launch task-server
```
The task server contains an RPyC interfact and by default listens on localhost's port 5000.
The host and port can be changed using the environment variables
`TRANSITER_TASKSERVER_HOST` and `TRANSITER_TASKSERVER_PORT` respectively.
It is critical that these variables are also set for the web server; otherwise,
the web server will be unable to contact the task server which can result
in feeds not being auto updated after a transit system install.
 
