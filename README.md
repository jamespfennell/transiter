The new real time rail project


API Endpoints: all under api/


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
