# Transiter TODO

## Main development thread
 
 
1. Things needed for realtimerail:
    1. In the get trip endpoint, show the station instead of
        the stop
    1. Detect no service - in routeservice#_constuct_status


1. All TODOs in the code and here are to me made as issues on github and 
removed here before v1!

1. Fix failing tests in NYC subway package 

Bug: sometimes the __eq__ method of _BasicModel
is called

## Version 0.2

1. Add logging

- Check the code coverage, and then write unit tests
    for the methods missing them
    
1. Existing code clean up
    - C6: Optimize the SQL ALchemy config
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



