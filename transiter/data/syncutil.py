"""
The sync util is used when syncing new data being imported into Transiter with
existing data in the database.

The problem this util solves is that in general the IDs found in a data feed
are only unique in the context of that data feed and not necessarily unique
in the Transiter instance as a whole. For example, while in a single GTFS static
feed each stop ID is unique, the GTFS static feed for one transit system (say
the NYC Subway) may contain stop IDs that are identical to stop IDs found in the
GTFS static feed for another transit system (say the Chicago metro). This is
why in Transiter IDs are only ever contextually unique, while PKs are always
globally unique.

When syncing data then, we cannot identify preexisting entities in the database
using the IDs in the feed alone. Instead, we return from the database all
entities that are potentially in the feed, and then compare the IDs in the
feed with those of teh entities in this limited set. For example, when performing
a GTFS realtime update for a transit system, we compare the trips IDs in the
feed with the IDs of all trips for that transit system that are already in the DB.

The sync util contains a method to perform this comparison and copy PKs over
to the entities in the DB. Once the PK is assigned to an entity, SQL Alchemy's
session::merge operation can be used to automatically handle reconciliation.
"""


def copy_pks(source_models, target_models, id_keys):
    """
    Copy the PKs from a set of source models (typically, entities that are
    already persisted in the database) to a set of target models (typically,
    entities that have been created from data in a data feed being imported),
    using a specific ID field in the model for linking target and source models.

    :param source_models: iterable of models
    :param target_models: iterable of models
    :param id_keys: a length-1 list where the unique element is a string
                    giving the name of the ID field in the models to use for
                    linking.
    :return: A three tuple containing the following:
             1. A list of source models that have no associated target model.
                These will often be subsequently deleted.
             2. A list of tuples (source model, target model) which have the
                same ID field. The PK of the source model will already be copied
                to the target model.
             3. A list of target models that have no associated source model.
                These will often be persisted in the database as new entities.
    """
    # TODO: id_keys should be just one id_field
    # NOTE: In this function we use dictionaries to gain the efficiency of sets
    # but without relying on a hash function being defined for the models
    if len(id_keys) > 1:
        raise NotImplementedError
    id_key = id_keys[0]
    new_models = {}
    updated_models = {}

    id_to_source_model = {getattr(model, id_key): model for model in source_models}

    for target_model in target_models:
        id_ = getattr(target_model, id_key)
        source_model = id_to_source_model.get(id_, None)
        if source_model is None:
            new_models[id_] = target_model
        else:
            target_model.pk = source_model.pk
            updated_models[id_] = (target_model, source_model)
            del id_to_source_model[id_]

    return (
        list(id_to_source_model.values()),
        list(updated_models.values()),
        list(new_models.values()),
    )
