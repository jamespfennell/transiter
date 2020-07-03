# Admin


These endpoints are used for administering the Transiter instance.

## Transiter health status

`GET /admin/health`


Return Transiter's health status.
This describes whether or not the scheduler and executor cluster are up.

## List scheduler tasks

`GET /admin/scheduler`


List all tasks that are currently being scheduled by the scheduler.

This contains the feed auto update tasks as well as the cron task that trims old feed updates.

## Refresh scheduler tasks

`POST /admin/scheduler`


When this endpoint is hit the scheduler inspects the database and ensures that the right tasks are being scheduled
and with the right periodicity, etc.
This process happens automatically when an event occurs that
potentially requires the tasks list to be changed, like a system install or delete.
This endpoint is designed for the case when an admin manually edits something in the database and
wants the scheduler to reflect that edit.

## Upgrade database

`POST /admin/upgrade`


Upgrades the Transiter database to the schema/version associated to
the Transiter version of the webservice.
This endpoint is used during Transiter updates: after first updating
the Python code (or Docker contains), this endpoint can be hit to
upgrade the database schema.
It has the same effect as the terminal command:

    transiterclt db upgrade
