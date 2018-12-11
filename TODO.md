# Transiter TODO

## Main development thread



- Check the code coverage, and then write unit tests
    for the methods missing them


data/
    database.py
    genericmethods.py
    feeddata.py
    routedata.py
    stopdata.py
    tripdata.py
    systemdata.py
    servicepatterndata.py
    ...
http/
    endpoints/
services/
    update/
        updatemanager.py <- both system and feed call this
            execute_feed_update
            update_system
        gtfsstaticreader.py
        gtfsrealtimereader.py
        tripupdater.py
    servicepattern/
        servicepatternmanager.py
        graph/
            pathstitcher.py
general/
    linksutil.py
    exceptions.py
    
taskserver/
    
1. Refactoring:
    1. New data access layer setup
        - Should not be too hard, mostly moving things around
        - merge connection and creator into database.py
    1. Use the new data access layer to fix Travis issues with the integration
        test
        
  
1. Go through all of the API endpoints and implement anything that's
    not implemented and make sure the docs are right

1. Add logging

1. Existing code clean up
    - C6: Optimize the SQL ALchemy config
        - especially with joins/lazy loading
        - Just adding .join(Model.attribute) loads it I think?
        https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html
        look at lazy
        
        For example, when getting stop events get the trip and stop as well
        
        cascade = None
      
    - C11:
    Bug: I'm transforming IS_ASSIGNED to a status, 
        but then overwriting that status in vehicle...this is an NYC subway specific
        problem at least and only relevant for trips without a vehicle entity
        Potentially it's fine, just make sure
        
        Maybe we can map it to an actual GTFS status though
    - C13:
        problem with the xml update - like a race condition when the message changes?
        Need this to also do models now




---I THINK IT WOULD BE GOOD TO HAVE MORE THAN 90% TESTING COVERAGE
BEFORE VERSION 0.2---NOW OR NEVER!


- All TODOs in the code and here are to me made as issues on github and 
removed here before v1!

- Fix and file a bug ticket with sql alchemy?

## Version 0.2

origin/terminus for trips - should not be in the DB but may be useful in some endpoints like stop

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
    - Updating system static data
    - Calculating route service patterns (if enabled)
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



