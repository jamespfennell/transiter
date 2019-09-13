
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

Getting started with Transiter is easy, and requires
only that you have Docker installed.
After checking out the Github repo, in the root directory run:

    docker-compose up
    
This will build Transiter's Docker images and launch the 
whole service on localhost's port 8000.
You can verify it's working by running,

    curl localhost:8000
    
which should yield a response like,

    {
      "transiter": {
        "version": "0.2.0",
        "href": "https://github.com/jamespfennell/transiter"
      },
      "systems": {
        "count": 0
      }
    }
    
As you can see, there are no transit systems installed and the 
next step is to install one.
To try out Transiter we suggest installing the San Francisco BART
system as it's fairly simple to install.
Follow the instructions in that Github repo.


        


## Docs

    pip install transiter
    
The current focus is on producing documentation so
Transiter can actually be used.

[Documentation website](https://docs.transiter.io).

## Development indicators

[![Build Status](https://travis-ci.org/jamespfennell/transiter.svg?branch=master)](https://travis-ci.org/jamespfennell/transiter)
[![Documentation Status](https://readthedocs.org/projects/transiter/badge/?version=latest)](https://docs.transiter.io)
[![Coverage Status](https://coveralls.io/repos/github/jamespfennell/transiter/badge.svg?branch=master&service=github)](https://coveralls.io/github/jamespfennell/transiter?branch=master) 

