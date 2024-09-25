from unibas.common.environment import TestEnvVariables, OpenAiEnvVariables, MongoAtlasEnvVariables

try:
    assert OpenAiEnvVariables.conn_id is None
    assert MongoAtlasEnvVariables.conn_id is None

    env_vars = []
    with open('.env') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split('=', 1)
            env_vars.append({'name': key, 'value': value})

    for env_var in env_vars:
        name, value = env_var['name'], env_var['value']
        _clean_name = name.lower().replace('test_', '')
        if value != '' and value is not None:
            setattr(TestEnvVariables, _clean_name, value)

except AssertionError as assertion_error:
    print('Warning! The local unittest module is imported in the airflow environment. This should not happen.')

