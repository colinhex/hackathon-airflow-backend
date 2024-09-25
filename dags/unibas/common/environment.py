import os


class OpenAiEnvVariables:
    conn_id: str = os.getenv('AIRFLOW_OPEN_AI_CONN_ID')
    embedding_model: str = os.getenv('AIRFLOW_OPEN_AI_EMBEDDING_MODEL')
    llm_model: str = os.getenv('AIRFLOW_OPEN_AI_LLM_MODEL', 'gpt-4o-mini')
    test_api_key: str = os.getenv('OPEN_AI_TEST_API_KEY')


class TestEnvVariables:
    """
    Test environment variables, are none in the airflow environment.
    """
    atlas_conn_string: str = os.getenv('TEST_ATLAS_CONN_STRING')
    vector_database: str = os.getenv('TEST_ATLAS_VECTOR_DATABASE')
    embeddings_collection: str = os.getenv('TEST_ATLAS_VECTOR_EMBEDDINGS_COLLECTION')
    airflow_database: str = os.getenv('TEST_ATLAS_AIRFLOW_DATABASE')
    batch_collection: str = os.getenv('TEST_ATLAS_AIRFLOW_BATCH_COLLECTION')
    open_ai_api_key: str = os.getenv('TEST_OPEN_AI_API_KEY')
    embedding_model: str = os.getenv('TEST_OPEN_AI_EMBEDDING_MODEL')
    llm_model: str = os.getenv('TEST_OPEN_AI_LLM_MODEL')


class MongoAtlasEnvVariables:
    conn_id: str = os.getenv('AIRFLOW_ATLAS_CONN_ID')
    vector_database: str = os.getenv('AIRFLOW_ATLAS_VECTOR_DATABASE')
    embeddings_collection: str = os.getenv('AIRFLOW_ATLAS_VECTOR_EMBEDDINGS_COLLECTION')
    airflow_database: str = os.getenv('AIRFLOW_ATLAS_AIRFLOW_DATABASE')
    batch_collection: str = os.getenv('AIRFLOW_ATLAS_AIRFLOW_BATCH_COLLECTION')


class ModelDumpVariables:
    STRINGIFY_DATETIME = 'stringify_datetime'
    STRINGIFY_OBJECT_ID = 'stringify_object_id'
    STRINGIFY_URL = 'stringify_url'


class ResourceVariables:
    RESOURCE_TYPE_FIELD = "resource_type"
    HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
