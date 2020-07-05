# Database upgrade test

This test verifies that the Alembic migrations can be run from
    a specific database dump.
This test cannot account for all possible data states and resulting
    migration problems, but it should deal with a large proportion them.
    
It was introduced in 0.5.1 after it was realized that one of the 
    Alembic migrations in 0.5.0 failed on Transiter databases that
    had realtime trip data in them.
    
To update the dump, run:
```text
pg_dump --format=custom -U transiter transiter > db.dump
```