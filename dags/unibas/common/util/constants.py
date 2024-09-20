import os

from unibas.common.typing import ConnectionId, EmbeddingModel, LlmModel, Text


class OpenAi:
    conn_id: ConnectionId = os.getenv('AIRFLOW_OPEN_AI_CONN_ID')
    embedding_model: EmbeddingModel = os.getenv('AIRFLOW_OPEN_AI_EMBEDDING_MODEL')
    llm_model: LlmModel = os.getenv('AIRFLOW_OPEN_AI_LLM_MODEL')


class MongoAtlas:
    conn_id: ConnectionId = os.getenv('AIRFLOW_ATLAS_CONN_ID')
    vector_database: Text = os.getenv('AIRFLOW_ATLAS_VECTOR_DATABASE')
    embeddings_collection: Text = os.getenv('AIRFLOW_ATLAS_VECTOR_EMBEDDINGS_COLLECTION')
    airflow_database: Text = os.getenv('AIRFLOW_ATLAS_AIRFLOW_DATABASE')
    batch_collection: Text = os.getenv('AIRFLOW_ATLAS_AIRFLOW_BATCH_COLLECTION')
