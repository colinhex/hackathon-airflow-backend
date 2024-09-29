from airflow.providers.mongo.hooks.mongo import MongoHook
from pymongo import MongoClient
from pymongo.collection import Collection

from unibas.common.environment.variables import TestEnvVariables, MongoAtlasEnvVariables


def _get_mongo_client() -> MongoClient:
    """
    Retrieve a MongoDB client instance.

    This function first checks for a test connection string in the environment variables.
    If a test connection string is found, it returns a MongoClient initialized with that string.
    Otherwise, it retrieves the MongoClient using the connection ID from the environment variables.

    Returns:
        MongoClient: An instance of the MongoDB client.
    """
    test_conn_string = TestEnvVariables.atlas_conn_string
    if test_conn_string is not None:
        return MongoClient(test_conn_string)
    return MongoHook(conn_id=MongoAtlasEnvVariables.conn_id).get_conn()


def on_collection(database: str, collection: str) -> Collection:
    return _get_mongo_client().get_database(database).get_collection(collection)


def on_batch_collection() -> Collection:
    return on_collection(MongoAtlasEnvVariables.airflow_database, MongoAtlasEnvVariables.batch_collection)


def on_embedding_collection() -> Collection:
    return on_collection(MongoAtlasEnvVariables.vector_database, MongoAtlasEnvVariables.embeddings_collection)