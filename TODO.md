# Transiter TODO

## Main development thread
Bugs:
  Service maps always rewrite. For the moment, just compute the new map and if
  it's identical do nothing

1. Code quality:
    1. Clean up the code where relevant
    1. Add tests for relevant things
            -> all tests had docstring
    1. Add docs
    1. Remove all TODOs - resolve or make Github issues
    1. Document the API correctly
    1. Does the RTR app still work? Likely not!

Random modules:

    ./general/config.py
    ./general/linksutil.py
    ./general/clt.py
    ./general/exceptions.py
    ./http/responsemanager.py (--> httpmanager)
    ./http/inputvalidator.py (delete/move into response manager/http manager)
    ./taskserver/server.py
    ./taskserver/client.py
    ./data/database.py

The update modules:

    ./services/update/routestatusupdater.py (rename alertupdater.py)
    ./services/update/gtfsstaticutil.py
    ./services/update/gtfsrealtimeutil.py
    ./services/update/tripupdater.py
    ./services/update/updatemanager.py

Create of service maps:

    ./services/servicepattern/graphutils/pathstitcher.py
    ./services/servicepattern/graphutils/graphdatastructs.py
    ./services/servicepattern/servicepatternmanager.py

Service. Do the endpoint after. Should just be updating the docs;
already at 100% test coverage there:

    ./http/flaskapp.py
    
    ./services/stopservice.py
    ./http/endpoints/stopendpoints.py
    
    ./services/tripservice.py
    ./http/endpoints/tripendpoints.py

Data. would be nice to have the tests passing on SQLLite...

    ./data/fastoperations.py
    ./data/dams/tripdam.py
    ./data/dams/servicepatterndam.py
    ./data/dams/genericqueries.py
    ./data/dams/routedam.py
    ./data/dams/stopdam.py
    ./data/dams/feeddam.py
    ./data/dams/systemdam.py

Models: mainly just safely renaming after we have close to 100% test coverage
Also change how short_repr works

    ./models/servicemapgroup.py
    ./models/system.py
    ./models/servicepatternvertex.py
    ./models/servicepattern.py
    ./models/servicepatternedge.py
    ./models/stoptimeupdate.py
    ./models/routestatus.py
    ./models/feedupdate.py
    ./models/scheduledservice.py
    ./models/route.py
    ./models/stop.py
    ./models/trip.py
    ./models/feed.py
    ./models/scheduledtripstoptime.py
    ./models/directionnamerule.py
    ./models/scheduledtrip.py
    ./models/base.py


## Version 0.2

1. Record the git hash outside of the Git repo for deployments ... 
    maybe when building the egg?

1. Investigate using Arrow

1. Add logging

1. Existing code clean up
    - C6: Optimize the SQL Alchemy config
        - especially with joins/lazy loading
        - Just adding .join(Model.attribute) loads it I think?
        https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html
        look at lazy
        
        For example, when getting stop events get the trip and stop as well
        
        cascade = None
      

#### F4: Write the Feed Health Code
How to delete old entries?
Just delete old entries when updating?
Yes - have the time a configuration parameter

Do we need feed health to be like this?
Can we just delete old feed updates when updating
and generate reports dynamically? 

#### F6: Feed autoupdaters
- Rename it Jobs Executor   
- Should probably have a more generic Jobs scheme:
    - Updating feeds
    - Calculating realtime route service patterns (if enabled)
    - Calculating the feed health (and deleting old entries)
        - Generating FeedHealthReport types
    
#### F7: Add a verbose option to route and stop GET endpoints

- In general, figure out a full set of extra GET parameters
   
### Features
- Service pattern endpoints and the edges table
- write the optimized topological 
sort algorithm for generating service patterns
- Make a system to download the latest GTFS static data 
    from the transit agency
    and check if it's up to date.
    - If it's not, what happens? 
    Maybe use the sync util carefully to allow updates <- just use a feed with
        default gtfsstatic parser
- How does a user/admin make stops? 
    - Admin service for
       finding stops based on geolocation
    - post and delete methods
- Have a generic get paremater that decides how times are to be read -
    timestamp, diff from now, human readable
- Support for trip schedules/general gtfs static data
- Get parameter to show all service patterns at a stop


    
- Integration test:
    write three separate test runs:
        - gtfs static import 
        - gtfs realtime import (stops)
        - gtfs realtime import (trips)
        
Last 2 only run if first succeeeds
clean it up in general



