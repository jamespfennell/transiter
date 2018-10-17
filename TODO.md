# Transiter TODO

## Main development thread

1. F6



## Version 0.1
    
### Features

#### F1: Have three separate Flask apps
1. Consumer app
2. Only GET endpoints app
3. All endpoints app

Think about how in deployments the admin app would be used
if only the consumer app is deployed.

#### F6: Feed autoupdaters
- Use APScheduler (Advanced Python Scheduler) to create runnables that
    can automatically update the feeds
    https://apscheduler.readthedocs.io/en/latest/userguide.html
    
    
- Should probably have a more generic Jobs scheme:
    - Updating feeds
    - Updating system static data
    - Calculating route frequencies
    - Calculating route service patterns (if enabled)
    - Calculating the feed health (and deleting old entries)
        - Generating FeedHealthReport types
    
#### F8: Implement href tags using an endpoint util
Can duplication be avoided in the flask app?


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
### Testing

 - Write unit tests for everything for the service layer and document the responses
    - aim for 100% test coverage, to be safe.
  - This incudes adding DB tests, for the daos
    - Testing with sqlalchemy:
    https://www.oreilly.com/library/view/essential-sqlalchemy-2nd/9781491916544/ch04.html

   - NOTE: It is important not to test things that are just part of the basic functionality of SQLAlchemy, 
   as SQLAlchemy already comes with a large collection of well-written tests. 
   For example, we wouldn’t want to test a simple insert, select, delete, or 
   update statement, as those are tested within the SQLAlchemy project itself. 
   Instead, look to test things that your code manipulates that could affect 
   how the SQLAlchemy statement is run or the results returned by it.



## Version 0.2


#### F2: Use YAML for configuring individual systems
Probably deprecate direction_name_exceptions.csv and put that in the
YAML. Or maybe an option to read it remotely

Or maybe have multiple csv file and infer the type from the headers
 

#### F4: Write the Feed Health Code
How to delete old entries?
Just delete old entries when updating?
Yes - have the time a configuration parameter

#### F5: Service Patterns
- Implement the DB layout
    - When loading static GTFS data, have a system for
        detecting nights/weekends/days/rush hours etc
        possibly using regex
    - Then have multiple route entries for each line.
    - But have a special route entries for the 'usual route'?
    - Take into consideration the 'usual routes' at a specifc
        stop, may be different. Though plan is to store
        these separate anyway...
    - Make ServicePatternEdge table
    - routelistutil -> servicepatternutil
   
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
- How does one make stations?
- System wide trip endpoints


    
