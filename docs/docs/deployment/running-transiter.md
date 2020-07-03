# Running Transiter


## Container based deployments

The simplest way to deploy Transiter is to use
containers along with the included configurations
for either Kubernetes (using the Transiter Helm Chart) or Docker compose.

During Transiter's continuous integration process, a
Docker image `jamespfennell/transiter:<version>`
 is built and uploaded to Docker hub.
    
Here `<version>` can be any of the following:

- For stable releases, this is the version number of the release; for example `0.3.1`.

- Setting `<version>` to be `latest` will spin up the most recent stable release.

- Setting `<version>` to be `dev-latest` will spin up the most recent green build on master.

For production settings, pinning to a fixed stable release is, of course, recommended.
The `latest` and `dev-latest` versions may introduce breaking API changes at any time.


### Kubernetes: the Transiter Helm Chart

The Transiter Helm Chart enables easy installation of 
Transiter on a Kubernetes cluster.

The Helm chart can be installed by referencing the built `tgz` file 
in GitHub:
```sh
helm install https://github.com/jamespfennell/transiter/raw/master/docker/helmchart-0.1.0.tgz
```
Or, by checking out the Git repository and installing from the file system:
```sh
helm install ./docker/helmchart
```


The Helm chart contains many configuration options.
These are defined and described in the 
[Helm Chart's values file](https://github.com/jamespfennell/transiter/blob/master/docker/helmchart/values.yaml).
Some particularly important options are as follows.

- The `version` is, by default, `latest`. As per the above, in production this should usually
    be overridden with a fixed version.
    
- If you are using custom feed parsers distributed as Python packages,
    these packages can be made available to Transiter using the 
    `pythonPackagesToProvide` option.

- By default the Postgres container does *not* use a persistent volume. 
    In production a persistent volume should be used so that data lives
    beyond the lifecycle of the container.
    This is configured in the `postgres.persistentVolume` configuration.


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

## Interlude: Transiter service topology

Transiter uses five Docker containers to run, as
well as an sixth init container:

1. The web service, which is a Gunicorn process 
    running inside of the Transiter Docker image.
    This can be replicated to support more HTTP traffic.
    
1. The scheduler, which is also a Gunicorn process 
    running inside of the Transiter Docker image.
    The scheduler can _not_ be replicated, as this will result in
     duplicated updates being executed.    
     
1. The executor, which is a Celery process
    running inside of the Transiter Docker image.
    This can be replicated to support more feed update processing throughput.
     
1. A Postgres instance, using the vanilla Postgres Docker image.
    This is where all the data lives.

1. A RabbitMQ instance, for the Celery cluster.
    This uses the vanilla rabbitmq Docker image.

1. The init container, which is based on the the Transiter Docker image.
    This container just initializes the database schema and then exits.
    
The topology is identical for non-Docker deployments, described below.

## Running Transiter without containers

Transiter can be run on "bare metal" and in development often is.
You system needs to have the following things installed:
Python 3.6+, Postgres and RabbitMQ.

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
transiterclt db reset
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
transiterclt launch webservice
```
This launches the Flask debugging server.


### Running the scheduler

The task server is responsible for scheduler periodic feed updates.
It is launched using:
```sh
transiterclt launch scheduler
```
The scheduler contains an HTTP interface and by default listens on localhost's port 5000.
The host and port can be changed using the environment variables
`TRANSITER_SCHEDULER_HOST` and `TRANSITER_SCHEDULER_PORT` respectively.
It is critical that these variables are also set for the web service and executor; otherwise,
the web service will be unable to contact the scheduler server which can result
in feeds not being auto updated after a transit system install.
 
### Running the executor

Simply:
```sh
transiterclt launch executor --logging-level info
```

