[![Coverage Status](https://coveralls.io/repos/github/jamespfennell/transiter/badge.svg?branch=master)](https://coveralls.io/github/jamespfennell/transiter?branch=master) [![Build Status](https://travis-ci.org/jamespfennell/transiter.svg?branch=master)](https://travis-ci.org/jamespfennell/transiter)

# Transiter

Transiter is a web service for distributing realtime transit information.
When deployed, Transiter consumes data from transit agencies (typically in
    GTFS realtime format), stores that data in a database and provides
    access to it through a simple REST API.

Transiter is currently in the initial development phase.
Version 0.1 will be somewhere between a refactor and a total rewrite of the
current backend of the realtimerail.nyc web app.

## API endpoints




feeds/
 - list all feeds
feeds/{feed_id}
 - get info on a feed: when last updated, url
feeds/{feed_id}/update
 - update the database based on a feed

routes/
 - list all routes with service status
route/{route_id}
 - return the information for a route

trips/
 - list all trips
trips/{trip_id}
 - return the information for a route

stops/
 - list all stops
stops/{stop_id}
 - return the information for a stop

(TODO v 1.1)
stations/
stations/{station_id}






@app.route('routes')
@cacheable - instead using app.before_request, app.after_request
 - see realtimerail.nyc/api/feeds/
@UnitOfWork
