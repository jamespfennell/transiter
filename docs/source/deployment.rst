Introductory guide to using Transiter
=====================================



Getting started
---------------


Requirements
~~~~~~~~~~~~~~~

- **Python 3.6**. This guide assumes that you're working inside a
  Python virtual environment.

- **Postgres**. Future versions of
  Transiter will support SQLite and possibly other databases systems,
  but Postgres is the only supported one in version 0.1.
  To use Transiter you should create a Postgres database;
  this can be done at the command prompt: ::

   psql -c "CREATE DATABASE transiter"


Installing Transiter
~~~~~~~~~~~~~~~~~~~~

Inside your virtual environment, install Transiter: ::

    pip install transiter

When you do this, you get three things.

1. A command line application :code:`transiterclt` ('Transiter command line tools').
   This contains a lot of different functionality and will be the only thing
   used in the *getting started* part of this guide.

2. A WSGI app located at :code:`transiter.wsgi_app`.
   This is used to run the Transiter HTTP server in production using
   Gunicorn or similar tools.

3. The :code:`transiter` Python package.
   The package itself is relevant if you need to write a custom feed parser
   for a Transit system you're interested in, or if you want to use Transiter
   functionality in a Python application in which case the HTTP layer can
   be completely bypassed.

After installing the software , the next
step is configure Transiter to use the Postgres database
created earlier. For this we need to create a Transiter configuration
file. To print a Transiter config file template in the console run::

    transiterclt generate-config

Let's instead write the config file to the default config location
*transiter-config.toml*: ::

    transiterclt generate-config -o transiter-config.toml

Using your text editor of choice, edit the database section of the config
to have the correct details.

.. note::

    When any Transiter service launches, the config file is first searched for.
    Transiter will first look in the environment variable
    :code:`TRANSITER_CONFIG` for a file path to the config.
    If the environment variable is set but the file cannot be found,
    Transiter will error out. If the environment variable is not set,
    then Transiter will search in the current working directory for the
    file *transiter-config.toml*. If that file doesn't exist, then Transiter
    will use the default SQLite configuration, which is currently not supported.
    So - always supply a config!


When the config is set up with the database details, the next
step is to initialize the Transiter database schema.
This is done by running::

    transiterclt rebuild-db

Note that if the Transiter database is already built, this command will
wipe out all of the data there!

With the database initialized, you can now run the debug Transiter
HTTP service::

    transiterclt launch http-debug-server


Installing your first Transit system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NOTE: right now the flask app is not visible outside the server!

The debug HTTP server launches on port 5000.
Navigating in your browser to the URL, ::

    http://localhost:5000/systems

you will get the following response::

    []

This should be interpreted as an empty JSON list,
and indicates that no transit systems are installed.

To install a transit system you need to provide a TOML config
file for that system. The config primarily specifies
where the data feeds for the transit system are be found.
This is an example of such a config for the BART system
in the San Francisco Bay Area::

    [details]
    name = 'BART'

    [feeds]

        [feeds.gtfsstatic]
        url = "https://www.bart.gov/sites/default/files/docs/google_transit_20180910_v13.zip"
        built_in_parser = "GTFS_STATIC"
        parser = "gtfsstatic"
        required_for_install = true
        auto_update = false

        [feeds.gtfsrealtime]
        url="http://api.bart.gov/gtfsrt/tripupdate.aspx"
        built_in_parser = "GTFS_REALTIME"
        auto_update = true
        auto_update_period = "15 seconds"

    [service_maps]

        [service_maps.any_time]
        source = 'schedule'
        threshold = 0.1
        use_for_stops_in_route = true
        use_for_routes_at_stop = true

        [service_maps.realtime]
        source = 'realtime'
        use_for_stops_in_route = true
        use_for_routes_at_stop = true

To install the BART system, save this config
on disk. Then perform the following HTTP request to the
Transiter server::

    curl -X PUT http://localhost:5000/systems/bart \
        -F 'config_file=@bart_config.toml'

The system will take a couple of seconds to install.
It can then be accessed at the URL,::

    http://localhost:5000/systems/bart

Running the task server
~~~~~~~~~~~~~~~~~~~~~~~

The Transiter task server is the easiest mechanism by which
to perform feed updates periodically.
It is launched using the :code:`transiterclt` tool::

    transiterclt launch task-server

If you have installed a Transit system with an auto-updating feed,
like the BART system above, you will see that feed updates are executed
periodically, and that up-to-date data is returned from the HTTP server.

Note that unlike the HTTP server, the task server is
designed to be used both when testing locally and in production.

Basic deployment
----------------

The HTTP and task servers in production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As was seen above, Transiter consists of two processes:
a HTTP process that responses to user HTTP requests, and background
task server that performs periodic feed updates.

Gunicorn::

     gunicorn transiter:wsgi_app

Gunicorn timeout issue

Transiter task server port needs to be an integer

Postgres - need to think about authentication

Supervisor configuration
~~~~~~~~~~~~~~~~~~~~~~~~

This is an example supervisor configuration::




    [group:transiter]
    programs=transiter-gunicorn-server,transiter-task-server

    [program:transiter-gunicorn-server]
    directory=/path/to/project
    command=./venv/bin/gunicorn transiter:wsgi_app
    environment=TRANSITER_CONFIG=transiter-config-postgres.toml
    autorestart=true
    stdout_logfile=logs/gunicorn-server.log
    redirect_stderr=true

    [program:transiter-task-server]
    directory=/path/to/project
    command=./venv/bin/transiterclt launch task-server
    environment=TRANSITER_CONFIG=transiter-config-postgres.toml
    autorestart=true
    stdout_logfile=logs/task-server.log
    redirect_stderr=true

Start using::

    supervisorctl start transiter:*

Nginx configuration
~~~~~~~~~~~~~~~~~~~
Nginx
 - placing in a subdirectory
 - only permitting admin read access