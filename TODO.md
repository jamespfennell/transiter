# Transiter TODO

## Main development thread

1. 
    Need some GTFS realtime data now
    Write an abstract class with a to_gtfs_realtime method
    Then can compares Transiter responses to that
    
    How about just a list of trips,stops, which then get converted based
        on the 'current time'
   
1. Refactoring:
    1. endpoints -> http
    1. DB rename:
        RENAME tables to singular -> easy
        Maybe the ORM mapping consistent in refering to object vs table
        Good time to rename stopevent -> stoptimeupdate
        Move pri_key to pk
        trip_id to id? yes
        stopalias -> stopidalias
    1. Move subway package out
    1. Move models to the main root dir
    1. New data access layer setup
    1. Use models as input to the sync utils 
        - C10: the sync util should use non-persisted models and then session.merge()
            - This means the GTFS util should output models and not JSON
            - Might be tricky to coordinate stop time update merging -> may need to 
                delete the stop events from the object first
            - Also need the XML Parser to have a convert to models step
            
  
1. Go through all of the API endpoints and implement anything that's
    not implemented
    - location, import from system service into location column
    - origin/terminus for trips 
        -> terminus should be dynamic
        -> origin a nullable foreign stop pri key



A full service test suite that hit every endpoint would be really really nice :)


Pull back in some of the NYC subway code that was removed
Add env variables to system config

## Version 0.1
    
### Features

#### F11: Add logging



### Existing code clean up
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
    - Calculating route frequencies
    - Calculating route service patterns (if enabled)
    - Calculating the feed health (and deleting old entries)
        - Generating FeedHealthReport types
    
#### F7: Add a verbose option to route and stop GET endpoints

#### F9: Add terminus abbr feature for NYC Subway
- Using the message table
- Also requires adding a terminus and origin field to each trip

#### F10: Refactor the NYC Subway code into its own package
   
### Features
- Service pattern endpoints and the edges table
- write the optimized topological 
sort algorithm for generating service patterns
- Make a system to download the latest GTFS static data 
    from the transit agency
    and check if it's up to date.
    - If it's not, what happens? 
    Maybe use the sync util carefully to allow updates
- Implement the stations endpoints.
- How does a user/admin make stations?
- System wide trip endpoints?
- Have a generic get paremater that decides how times are to be read -
    timestamp, diff from now, human readable
- Support for trip schedules/general gtfs static data
- Get parameter to show all service patterns at a stop


    
