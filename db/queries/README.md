# Query naming scheme

The `db.Querier` interface that `sqlc` generates has one method for each query.
At time of writing, there are over 100 queries and thus over 100 methods in this interface.
This makes auto-complete harder to use.
Even after typing some words in the method name,
    multiple methods will often be suggested and it's sometimes hard to know which is the right one.
(E.g., is it `ListRoutes` or `ListRoutesInSystem`?)

To help with this, the Transiter queries have a hopefully strict naming scheme.
This is currently a work-in-progress.
In the following, `X` is a Transiter entity like a system or a stop.

- `InsertX` - inserts an entity of type `X` in the database.
- `UpdateX` - updates an entity of type `X` in the database in general purpose way.
- `UpdateX_Fields` - updates specific fields of an entity of type `X` in the database.
- Usually one delete query, either:
    - `DeleteX` - deletes an entity of type `X` in the database using its primary key.
        This is generally used for entites whose lifecycle is managed outside of the feed update system.
    - `DeleteStaleXs` - deletes each entity of type `X` that was not updated in the most
        recent feed update for the entity's source feed.
        This is only used for entites whose lifecycle is managed using the feed update system.
- `ListXs` - lists entities of type `X` all having the same parent entity.
    For example, lists stops that are all in the same system.
    The parent entity is specified by its primary key.
    Other filtering conditions may be provided.
- `ListXs_Qualifier` - same as `ListXs`, but with different filtering or sorting.
- `ListXsByPk` - lists entites of type `X` using their primary keys.
- `ListXsByYs` - lists entites of type `X` based on their relationship to a non-parent entity `Y`.
    For example, `ListTripStopTimesByStop` lists trip stop times who have the same stop.
- `GetX` - gets an entity of type `X` by specifying its ID and the primary key of its parent.
- `MapXIDToPk`, `MapXPkToID`, `MapStopPkToChildPks`, etc. - 
    returns enough data to be able to map an ID or primary key field of `X` to some other ID or
    primary key field.
