# This module provides a registry for updatable entities.


def updatable_from(feed_entity):
    def decorator(cls):
        _db_entity_to_feed_entity[cls] = feed_entity
        return cls

    return decorator


def list_updatable_entities():
    return list(_db_entity_to_feed_entity.keys())


def list_feed_entities():
    return list(_db_entity_to_feed_entity.values())


def get_feed_entity(db_entity):
    return _db_entity_to_feed_entity[db_entity]


_db_entity_to_feed_entity = {}
