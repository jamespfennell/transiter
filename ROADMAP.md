
# Transiter road map

## Summary of the large-scale goals of versions 0.4 through 0.6

- 0.4: Address core technical deficiencies that make deploying
    and administrating Transiter instances difficult.
    This version will basically have no user facing features
    but will instead focus on purely technical objectives like enabling 
    Transiter instances
    to be updated in place.
    
- 0.5: Ensure Transiter has the minimal number of features
    that would be expected from its description. This largely means
    bringing full and complete GTFS static and realtime support and
    guaranteeing that most (all?) transit systems in North America (say) 
    can be installed on Transiter.

- 0.6: Introduce new Transiter features like timetable viewing,
    cross-transit-system stations and searching for stops by location.

## Version 0.4

Roughly in order of priority:

- More maintainable and scalable integration testing
    ([#18](https://github.com/jamespfennell/transiter/issues/18)).

- Introduce a Celery cluster and async endpoints.

- Migrate the "task server" to be a scheduler where tasks are
    executed on the Celery cluster.
    (will resolve
    [#27](https://github.com/jamespfennell/transiter/issues/27) and
    [#28](https://github.com/jamespfennell/transiter/issues/28)
    ).
    
- Introduce a settings DB table
    ([#22](https://github.com/jamespfennell/transiter/issues/22)).

- New schema installation procedure - remove the more custom Postgres Docker image.

- Refactor the DB tests be to less global and based on pytest fixtures.

- Jinja templating for transit system configs
    ([#47](https://github.com/jamespfennell/transiter/issues/47)).

- Feed flush and auto-flush feature
    ([#45](https://github.com/jamespfennell/transiter/issues/45)).

- Fast transit system deletes
    ([#21](https://github.com/jamespfennell/transiter/issues/21)).

- Enable updating transit systems
    ([#2](https://github.com/jamespfennell/transiter/issues/2)).

- Introduce an alembic DB migrations systems.

All other 0.4 labelled tickets will be addressed or closed without action.

## Version 0.5

## Version 0.6