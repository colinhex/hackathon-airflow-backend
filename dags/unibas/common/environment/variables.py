import os


class OpenAiEnvVariables:
    """
    Environment variables for OpenAI configuration.

    Attributes:
        conn_id (str): The connection ID for OpenAI.
        embedding_model (str): The embedding model to use.
        llm_model (str): The language model to use, defaults to 'gpt-4o-mini'.
        test_api_key (str): The API key for testing purposes.
    """
    conn_id: str = os.getenv('AIRFLOW_OPEN_AI_CONN_ID')
    embedding_model: str = os.getenv('AIRFLOW_OPEN_AI_EMBEDDING_MODEL')
    llm_model: str = os.getenv('AIRFLOW_OPEN_AI_LLM_MODEL', 'gpt-4o-mini')
    test_api_key: str = os.getenv('OPEN_AI_TEST_API_KEY')


class TestEnvVariables:
    """
    Test environment variables, are none in the Airflow environment.

    Attributes:
        atlas_conn_string (str): The connection string for Atlas.
        vector_database (str): The vector database name.
        embeddings_collection (str): The embeddings collection name.
        airflow_database (str): The Airflow database name.
        batch_collection (str): The batch collection name.
        open_ai_api_key (str): The API key for OpenAI.
        embedding_model (str): The embedding model to use.
        llm_model (str): The language model to use.
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
    """
    Environment variables for MongoDB Atlas configuration.

    Attributes:
        conn_id (str): The connection ID for MongoDB Atlas.
        vector_database (str): The vector database name.
        embeddings_collection (str): The embeddings collection name.
        airflow_database (str): The Airflow database name.
        job_collection (str): The batch collection name.
    """
    conn_id: str = os.getenv('AIRFLOW_ATLAS_CONN_ID')
    vector_database: str = os.getenv('AIRFLOW_ATLAS_VECTOR_DATABASE')
    embeddings_collection: str = os.getenv('AIRFLOW_ATLAS_VECTOR_EMBEDDINGS_COLLECTION')
    airflow_database: str = os.getenv('AIRFLOW_ATLAS_AIRFLOW_DATABASE')
    job_collection: str = os.getenv('AIRFLOW_ATLAS_AIRFLOW_JOB_COLLECTION')
    url_graph_collection: str = os.getenv('AIRFLOW_ATLAS_AIRFLOW_URL_GRAPH_COLLECTION')
