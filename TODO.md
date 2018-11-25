# Transiter TODO

## Main development thread





1. Fix the direction names csv file

1. Refactoring:
    1. endpoints -> http
    1. gtfsutil -> gtfsrealtimeutil
    1. Delete station and stop_id_alias
    1. Move models to the main root dir
    1. New data access layer setup
        - Should not be too hard, mostly moving things around
        - merge connection and creator into database.py
    1. Use models as input to the sync utils 
        - C10: the sync util should use non-persisted models and then session.merge()
            - This means the GTFS util should output models and not JSON
            - Might be tricky to coordinate stop time update merging -> may need to 
                delete the stop events from the object first
            - Also need the XML Parser to have a convert to models step
  
1. Go through all of the API endpoints and implement anything that's
    not implemented and make sure the docs are right
    - location, import from system service into location column? Or delete this field?
    - origin/terminus for trips 
        -> terminus should be dynamic
        -> origin should also just dynamic -> the first stop event
            should be nullable

1. Get the NYC package set up with automatic testing and CI (how to pull in transiter?)
1. 
    Need some GTFS realtime data now for integration test
    Write an abstract class with a to_gtfs_realtime method
    Then can compares Transiter responses to that
    
    How about just a list of trips,stops, which then get converted based
        on the 'current time'

1. Pull back in some of the NYC subway code that was removed into gtfs realtimeutil

1. Add logging
1. Existing code clean up
    - C6: Optimize the SQL ALchemy config
        - especially with joins
        - figure out what the cascades are doing
        - Just adding .join(Model.attribute) loads it I think?
        https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html
        look at lazy
        
        For example, when getting stop events get the trip as well
    - C8: Add uniqueness and not null conditions to the schema
        where possible. Also add good indices.
      
    - C11:
    Bug: I'm transforming IS_ASSIGNED to a status, 
        but then overwriting that status in vehicle...this is an NYC subway specific
        problem at least and only relevant for trips without a vehicle entity
        Potentially it's fine, just make sure
        
        Maybe we can map it to an actual GTFS status though
    - C13:
    problem with the xml update - like a race condition when the message changes?




---I THINK IT WOULD BE GOOD TO HAVE MORE THAN 90% TESTING COVERAGE
BEFORE VERSION 0.2---NOW OR NEVER!


## Version 0.2


#### F4: Write the Feed Health Code
How to delete old entries?
Just delete old entries when updating?
Yes - have the time a configuration parameter

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
    Maybe use the sync util carefully to allow updates
- How does a user/admin make stops? Admin service for
       finding stops based on geolocation
- System wide trip endpoints? For trips that have no route
- Have a generic get paremater that decides how times are to be read -
    timestamp, diff from now, human readable
- Support for trip schedules/general gtfs static data
- Get parameter to show all service patterns at a stop


    
