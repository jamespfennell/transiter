
# Transiter

Transiter is a webservice for accessing realtime transit data.
Transiter consumes GTFS static and realtime data from transit agencies
    and provides intuitive
    access to it through a HTTP REST API.
An example of a request that can be made to a running Transiter instance is
    "give me the next four trains that will stop at Union Square."


Transiter was designed to be the backend of transit time apps,
    train arrival boards, and other pieces of technology that
    display and use realtime transit data.
The benefits of using Transiter, rather than working
    with raw data feeds, include:

- Integration of static data 
    (station names, allowable free transfers, which routes regularly stop at the given station)
    with realtime vehicle arrival data.
    
- Access to information indirectly present in the data feeds.
    For example, Transiter will calculate the current frequency of each route
    ("L trains running every 5 minutes").
    Transiter can also use GTFS static data to automatically calculate
    the ordered list of stops served by each route.
    

Transiter is currently in the initial development phase.
Version 0.1 will be somewhere between a refactor and a total rewrite of the
current backend of the [realtimerail.nyc web app](https://www.realtimerail.nyc).

The [documentation for Transiter](https://docs.transiter.io)
is hosted on Read The Docs.

## Development indicators

[![Build Status](https://travis-ci.org/jamespfennell/transiter.svg?branch=master)](https://travis-ci.org/jamespfennell/transiter)
[![Documentation Status](https://readthedocs.org/projects/transiter/badge/?version=latest)](https://docs.transiter.io)
[![Coverage Status](https://coveralls.io/repos/github/jamespfennell/transiter/badge.svg?branch=master&service=github)](https://coveralls.io/github/jamespfennell/transiter?branch=master) 

## Deployment notes

- Install Postgres 
    - Create a user and allow them to create DBs
    - Set the username and DB name through environment variables, default
        to transiter/transiter.   
    -Then initialize the DB - how! Should add a command
    transiter-builddb.

- Install gunicorn and use supervisor to run the gunicorn process
    and the transiter-task process.
 
- Install nginx and reverse proxy to Gunicorn (post config)