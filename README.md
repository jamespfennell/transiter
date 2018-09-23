
# Transiter

Transiter is a web service for distributing realtime transit information.
Transiter consumes data from transit agencies
    and provides intuitive
    access to it through a simple REST API.

 - Instead of parsing feeds and extracting the tiny subset of data needed,
    the data can be accessed through API endpoints like
    "list the next ten trains stopping at World Trade Center."
- Transiter can be configured to read realtime data in any format,
    and comes GTFS Realtime support built in.
- Transiter also consume GTFS Static data and integrates
    this with realtime information.
- Historical stop data for each trip is preserved, so more information
    can be presented than is given in the (future data only)
     realtime feeds.

Transiter is currently in the initial development phase.
Version 0.1 will be somewhere between a refactor and a total rewrite of the
current backend of the [realtimerail.nyc web app](https://www.realtimerail.nyc).

The [documentation for Transiter](https://transiter.readthedocs.io/en/latest/)
is hosted on Read The Docs.

## Development indicators

[![Build Status](https://travis-ci.org/jamespfennell/transiter.svg?branch=master)](https://travis-ci.org/jamespfennell/transiter)
[![Documentation Status](https://readthedocs.org/projects/transiter/badge/?version=latest)](https://transiter.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/jamespfennell/transiter/badge.svg?branch=master)](https://coveralls.io/github/jamespfennell/transiter?branch=master) 

