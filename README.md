
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
        

## Getting started

The easiest way to get Transiter up and running is to
use Docker compose with the configuration file at 
[docker/docker-compose.yaml](https://raw.githubusercontent.com/jamespfennell/transiter/master/docker/docker-compose.yml). It references Docker images
that are stored in Docker Hub, so it will work immediately;
assuming it's in your current working directory, just run:

    docker-compose up

Building the Docker images themselves is also easy.
Checkout the Git repo and run:

    make docker
    
Then launch using Docker compose:

    docker-compose -f docker/docker-compose.yml up
    
Either approach will launch a Transiter service
listening for HTTP requests on localhost's port 8000.
Running

    curl localhost:8000
    
will yield a response like:

    {
      "transiter": {
        "version": "0.3.1",
        "href": "https://github.com/jamespfennell/transiter"
        "docs": {
            "href": "http://localhost:8000/docs/"
        }
      },
      "systems": {
        "count": 0,
        "href": "http://localhost:8000/systems"
      }
    }
    
As you can see, there are no transit systems installed and the 
next step is to install one.
The [San Francisco BART system](https://github.com/jamespfennell/transiter-sfbart)
 is simple to install:
assuming the steps above have been followed, simply execute:

    curl -X PUT "localhost:8000/systems/sfbart?sync=true" \
        -F 'config_file=https://raw.githubusercontent.com/jamespfennell/transiter-sfbart/master/Transiter-SF-BART-config.yaml'

The install will take a couple of seconds as the BART's 
schedule is loaded into the database.

If you are streaming the Docker compose 
output you'll notice after the install
 that realtime feed updates are now occurring every 5 seconds.
At this point you're ready to navigate the HTTP API to
access the BART's static and realtime data!
For example, to get data at the BART station
at San Francisco International Airport (stop ID `SFIA`), just execute:

    curl localhost:8000/systems/sfbart/stops/SFIA
        

## Possible next steps

- Install [the New York City Subway system](https://github.com/jamespfennell/transiter-nycsubway).
- Learn how to write [transit system config files](https://docs.transiter.io/docs/systems/) in order to add other transit systems to Transiter (it's very easy!)
- Write a [custom feed parser](https://docs.transiter.io/docs/feedparsers/) to import data in non-standard format into Transiter.
    
The [documentation website](https://docs.transiter.io) has much more
including advice on deployment.

## Development indicators

[![Build Status](https://travis-ci.org/jamespfennell/transiter.svg?branch=master)](https://travis-ci.org/jamespfennell/transiter)
[![Coverage Status](https://coveralls.io/repos/github/jamespfennell/transiter/badge.svg?branch=master&service=github)](https://coveralls.io/github/jamespfennell/transiter?branch=master) 
[![Requirements Status](https://requires.io/github/jamespfennell/transiter/requirements.svg?branch=master)](https://requires.io/github/jamespfennell/transiter/requirements/?branch=master)

