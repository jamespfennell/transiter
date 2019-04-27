# Transiter TODO
## Github issues:

- make the system service better at responding to bad system config.
    also, try to get the parser for the feed to ensure it's valid
    
- better feed back when the system can't be installed because of a feed update
    problem
- bug: if a custom module has an error, it's reported as if the module
    doesn't exist
    
- bug: feed update time reporting doesn't take into account
    the session closing
    
- bug: fix the graph data structures. Probably need a b
# TODO: what about circle graphs? These appear as empty graphs


- add source to stop and route and trip
important for trips!!
    
- investigate our handling of time. Make cross DB platform 
    Also America/New York is hardcoded in  
       Investigate using Arrow
     Especially in the GTFS realtime util
     The most important thing is that end to end is the identity
     we seem to be using postgres time types.....
     
   - also docformatter
     
- Put the feed time in the FeedUpdate?


- figure out how the protobuf extension actually works

- full GTFS static and realtime


- make a transiter GTFS realtime extension

-replace direction name rules with stop head sign and
    have a custom parser that populates these? would need
    to be on static and realtime import
- investigate lazy loading of SQL alchemy enities
## Main development thread

1. Code quality:
    1. Clean up the code where relevant
    1. Add tests for relevant things
            -> all tests had docstring
    1. Add docs
    1. Remove all TODOs - resolve or make Github issues
    1. Document the API correctly
    1. Does the RTR app still work? Likely not!



Creation of service maps:
rename to servicemaps

    ./services/servicepattern/servicepatternmanager.py

Data. would be nice to have the tests passing on SQLLite...?
Also need to fix the bug on the SQL Alchemy upgrade.
 Maybe it's this: https://github.com/sqlalchemy/sqlalchemy/issues/4538
***Return no iterators from the database layer***
Check that queries are actually being used

    ./data/database.py (-> database/connection.py?)
    ./data/fastoperations.py
    ./data/dams/tripdam.py
    ./data/dams/servicepatterndam.py
    ./data/dams/genericqueries.py
    ./data/dams/routedam.py
    ./data/dams/stopdam.py
    ./data/dams/feeddam.py
    ./data/dams/systemdam.py

The task server:
Can we run multi process and get around warnings about 123456?
Also suppress the warnings! <- This. we should support refreshing the 
feed at a smaller periodicity than the feed update takes
Workaround is to increase the refresh time

    ./taskserver/server.py
    ./taskserver/client.py
    
Models: mainly just safely renaming after we have close to 100% test coverage
Also change how short_repr works
add string repr?
Add various DB constraints

    ./models/servicemapgroup.py
    ./models/system.py
    ./models/servicepatternvertex.py
    ./models/servicepattern.py
    ./models/servicepatternedge.py
    ./models/stoptimeupdate.py (-> tripstoptime.py)
    ./models/routestatus.py (-> alert.py)
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



1. Record the git hash outside of the Git repo for deployments ... 
    maybe when building the egg?
Incorporate this into building and distributing the App


Final (?) 0.1 bug: the fast scheduled entites inserter doesn't just 
get the id_to_pk map for the current system
Need a scheduledam probably

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



