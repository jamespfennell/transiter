
# Transiter

[![7 train in Queens, New York, United States](7-train-in-queens-new-york.jpg "Photo by Luca Bravo")](https://unsplash.com/@lucabravo)

Transiter is a HTTP web service that makes it easy to use 
transit data in web apps, train arrival time boards and similar technologies.

Transiter subscribes to GTFS static, GTFS realtime and other types of feeds
    and provides integrated views of the data through an intuitive REST API.
The endpoint for a particular stop, for example,
    returns the stop's static data (such as its name and GPS coordinates),
    its realtime data (the list of vehicles that will arrive next,
        and the times they will arrive),
    as well as derived data that Transiter computes automatically,
        such as which routes usually call at the stop,
        which transfers to other stops are available,
        and which routes are currently calling at *those* stops.
You can get a sense for the data that's available by navigating through the 
    [live demo site](https://demo.transiter.io).
        

    

Transiter is currently in the initial development phase.
Version 0.1 will be somewhere between a refactor and a total rewrite of the
current backend of the [realtimerail.nyc web app](https://www.realtimerail.nyc).

[Documentation for Transiter](https://docs.transiter.io) (lots of work to be done here).

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