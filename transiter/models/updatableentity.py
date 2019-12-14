# This module provides a registry for updatable entities.


def updatable_entity(cls):
    _updatable_entities.append(cls)
    return cls


def list_updatable_entities():
    return _updatable_entities


_updatable_entities = []
