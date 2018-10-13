# Transiter TODO

## Main development thread

1. Continue C2 by 
    - then write small tests for deep dive debugging, these should give 100% cov
    - For the merge in function:
        - write small tests for the bit of functionality
    - DO the same class break up for the clean function
        - write small tests for the whole thing, no need to try individual functions
1. C9
1. F3
1. F4



## Version 0.1

    
### Features

#### F1: Have three separate Flask apps
1. Consumer app
2. Only GET endpoints app
3. All endpoints app

Think about how in deployments the admin app would be used
if only the consumer app is deployed.

#### F2: Use YAML for configuring individual systems
Probably deprecate direction_name_exceptions.csv and put that in the
YAML. Or maybe an option to read it remotely

#### F3: Rewrite the NYC Subway priority code
Right now that priorities stated by the feed are not great.
Manually override them using also the message type.

Probably a good time to redo the message table to ensure its
serving use cases correctly

Improve/clean up the NYC Subway xml file parser
as part of this task

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
    
#### F6: Feed autoupdaters
- Use APScheduler (Advanced Python Scheduler) to create runnables that
    can automatically update the feeds
    https://apscheduler.readthedocs.io/en/latest/userguide.html
    
#### F7: Add a verbose option to route and stop GET endpoints

#### F8: Implement href tags using an endpoint util
Can duplication be avoided in the flask app?

#### F9: Add terminus abbr feature for NYC Subway
- Using the message table

#### F10: Refactor the NYC Subway code into its own package
   
### Existing code clean up
- C2: Move the trip sync function from gtfsutil to syncutil. Clean up both and write
        tests for both utils -- looks like sqlalchemy tests not needed!
        Just need to ensure it's calling the delete function
        and populating the new models and updating 
        the existing one.
        - So for the basic sync there are 3 cases
        if we can assume everything is independent
        Could iterate over all 8 combinations of each missing or not
- C6: Optimize the SQL ALchemy config
    - especially with joins
    - figure out what the cascades are doing
    - Just adding .join(Model.attribute) loads it I think
- C7: find out when SQL Alchemy triggers updates 
    and use this to inform the sync method. This should be doable manually
- C8: Add uniqueness and not null conditions to the schema
    where possible.
- C9: split the daos into separate modules and initialize them
    in the modules

### Testing

 - Write unit tests for everything for the service layer and document the responses
    - aim for 100% test coverage, to be safe.
  - This incudes adding DB tests, for the daos
    - Testing with sqlalchemy:
    https://www.oreilly.com/library/view/essential-sqlalchemy-2nd/9781491916544/ch04.html


   - NOTE: It is important not to test things that are just part of the basic functionality of SQLAlchemy, as SQLAlchemy already comes with a large collection of well-written tests. For example, we wouldn’t want to test a simple insert, select, delete, or update statement, as those are tested within the SQLAlchemy project itself. Instead, look to test things that your code manipulates that could affect how the SQLAlchemy statement is run or the results returned by it.



## Version 0.2

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


    
