from transiter.data import database


def copy_pks(source_models, target_models, id_keys, pk_key='pk'):
    # In this function we use dictionaries to gain the efficiency of sets
    # but without relying on a hash function being defined for the models
    new_models = {}
    updated_models = {}

    def model_id(model):
        return tuple(getattr(model, id_key) for id_key in id_keys)

    id_to_source_model = {model_id(model): model for model in source_models}

    for target_model in target_models:
        id_ = tuple(getattr(target_model, id_key) for id_key in id_keys)
        source_model = id_to_source_model.get(id_, None)
        if source_model is None:
            new_models[id_] = target_model
        else:
            target_model.__setattr__(pk_key, getattr(source_model, pk_key))
            updated_models[id_] = (target_model, source_model)
            del id_to_source_model[id_]

    return (
        list(id_to_source_model.values()),
        list(updated_models.values()),
        list(new_models.values()),
    )


