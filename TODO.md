# Transiter TODO

## Main development thread

RENAME tables to singular -> easy
Maybe the ORM mapping consistent in refering to object vs table
Good time to rename stopevent -> stoptimeupdate
Move pri_key to pk
trip_id to id?


1. Bring in the YAML config
1. Right the matcher generator function
1. Apply the matching generator
1. Revamp directions names:
    1. Direction name rules
    1. In direction names, use stop alias rather than direction? Or also direction_id
    1. introduce a priority system to rules matching
1. Go through all of the API endpoints and implement anything that's
    not implemented
    - usual_service -> need service patterns for this
        because the route entry doesn't give the usual service
    - location, import from system service into location column
    - origin/terminus for trips 
        -> terminus should be dynamic
        -> origin a nullable foreign stop pri key





SELECT 
    MIN(stop_events.arrival_time) as first_arrival_time,
    MAX(stop_events.arrival_time) as last_arrival_time,
    COUNT(*) as number_of_trips,
    stop_events.stop_pri_key
FROM routes
INNER JOIN trips
    ON trips.route_pri_key = routes.id
INNER JOIN stop_events 
    ON stop_events.id = (
        SELECT id 
        FROM stop_events
        WHERE trip_pri_key = trips.id
        ORDER BY arrival_time DESC
        LIMIT 1
    )
WHERE routes.route_id = '1'
GROUP BY stop_events.stop_pri_key;





Other solution: group by trip to get the max, and then join back in the
    row to get the stop


SELECT stops.stop_id, routes.route_id
FROM stops
INNER JOIN service_pattern_vertices
    ON stops.id = service_pattern_vertices.stop_pri_key
INNER JOIN service_patterns
    ON service_pattern_vertices.service_pattern_pri_key = service_patterns.id
INNER JOIN routes
    ON routes.default_service_pattern_pri_key = service_patterns.id
WHERE stops.stop_id IN ('635', 'L03');



CREATE INDEX index_name_trip_arrival_time
ON stop_events (trip_pri_key, arrival_time);



CREATE INDEX index_name_trip_arrival_time_two_mundo
ON trips (route_pri_key);





## Version 0.1
    
### Features

#### F1: Have three separate Flask apps
1. Consumer app
2. Only GET endpoints app
3. All endpoints app

Think about how in deployments the admin app would be used
if only the consumer app is deployed.

What happens to the links if the endpoint is not in the app

#### F5: Service Patterns
- Implement the DB layout
    - Make ServicePatternEdge table
   


#### F11: Add logging



### Existing code clean up
- C2: Continue cleaning up sync util:
    - See if the syncuti.synctrips can be refactored
        - maybe place it in a tripsupdaterutil
    - Write tests for it
    - Write more tests for the gtfs cleaner to get full coverage
    - Merge in the functions at the end into the cleaner
    - Write the cleaner that switches the directions on the J or M train
- C6: Optimize the SQL ALchemy config
    - especially with joins
    - figure out what the cascades are doing
    - Just adding .join(Model.attribute) loads it I think?
    https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html
    look at lazy
- C8: Add uniqueness and not null conditions to the schema
    where possible. Also add good indices.
- C10: the sync util should use non-persisted models and then session.merge()
    - This means the GTFS util should output models and not JSON
    - Might be tricky to coordinate stop time update merging -> may need to 
        delete the stop events from the object first
    - Also need the XML Parser to have a convert to models step
  

- C11:
Bug: I'm transforming IS_ASSIGNED to a status, 
    but then overwriting that status in vehicle...this is an NYC subway specific
    problem at least and only relevant for trips without a vehicle entity
    Potentially it's fine, just make sure
- C12:
    investigate testing the daos
- C13:
    problem with the xml update - like a race condition when the message change?




---I THINK IT WOULD BE GOOD TO HAVE MORE THAN 90% TESTING COVERAGE
BEFORE VERSION 0.2---NOW OR NEVER!


## Version 0.2


#### F2: Use YAML for configuring individual systems
Probably deprecate direction_name_exceptions.csv and put that in the
YAML. Or maybe an option to read it remotely

Or maybe have multiple csv file and infer the type from the headers
 
Have a priority on the direction names 


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
- Service pattern endpoints 
- write the optimized topological 
sort algorithm for generating routes lists.
    (Also, better name than route lists?)
- Make a system to download the latest GTFS static data 
    from the transit agency
    and check if it's up to date.
    - If it's not, what happens? 
    Maybe use the sync util carefully to allow updates
- Implement the stations endpoints.
- How does a user/admin make stations?
- System wide trip endpoints
- Have a generic get paremater that decides how times are to be read -
    timestamp, diff from now, human readable
- Support for trip schedules


    
