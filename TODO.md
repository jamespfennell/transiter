# Transiter TODO

## Main development thread

 1. Double check all of the endpoints match the API with
    appropriate not implemented flags. Update the API and services
    as appropriate to get 100% consistency

## Version 0.1

### Testing

 - Write unit tests for everything - aim for 100% test coverage, 
    to be safe.
  - This incudes adding DB tests, especially for the GTFS Realtime DB sync code.
    - Testing with sqlalchemy:
    https://www.oreilly.com/library/view/essential-sqlalchemy-2nd/9781491916544/ch04.html
 - add the terminus abbr table and load the data. Can this be done in a way
    that is not so specific to the NYC subway? Maybe the message table?
    Yes - only needed in the update step
    
### Features
- Have three separate apps:
    - read only
    - non admin
    - all
- Use YAML for configiguring the subway
- Rewrite the NYC subway status priority code to make it
    actually workable
- Write the feed health code. Might need a feed runnable
    that deletes the old data?
- Implement the 'route list entries' DB layout to actually
    make it usable
    It's actually called ServicePattern
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
- Use APScheduler (Advanced Python Scheduler) to create runnables that
    can automatically update the feeds
    https://apscheduler.readthedocs.io/en/latest/userguide.html
    - Aka, implement the autoupdate feature.
- Add a verbose option to route and stop get endpoints
- In feeds add an ALLOW_EMPTY_CONTENT flag
    
### Existing code clean up
- Rename the representation short_repr and long_repr?
- Rename DB columns
- Move the trip sync function from gtfsutil to syncutil
- Rewrite the install and update systems to use the new DAOs
- Improve/clean up the NYC Subway xml file parser.
- Optimize the SQL ALchemy config, especially with joins
    and figure out what the cascades are doing
    Just adding .join(Model.attribute) loads it I think
- Make Daos singletons?
- find out when SQL Alchemy triggers updates 
    and use this to inform the sync method.
- Add uniqueness and not null conditions to the schema
    where possible.
- Speed up sync_trip_data by doing one query to retrieve
    all relevent stop_events.


### The package refactor

- Have two packages transitor and transiter_nycsubway
- THe transitor package comes with a YAML config file



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
- Add the complexes feature (i.e., collections of stations
    spanning multiple transit systems).
- Implement the stations endpoints.



    
