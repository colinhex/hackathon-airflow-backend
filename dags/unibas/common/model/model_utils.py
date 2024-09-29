

def dump_all_models(models):
    return [model.model_dump(by_alias=True) for model in models]


def dump_all_models_json(models):
    return [model.model_dump_json(by_alias=True) for model in models]