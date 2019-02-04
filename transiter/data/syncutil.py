def copy_pks(source_models, target_models, id_keys):
    # In this function we use dictionaries to gain the efficiency of sets
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


