from airflow.providers.mongo.hooks.mongo import MongoHook
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.results import InsertManyResult, UpdateResult, DeleteResult
from typing_extensions import Dict, Any

from unibas.common.environment.variables import TestEnvVariables, MongoAtlasEnvVariables
from unibas.common.model.model_mongo import MongoQuery, FindOneResult, FindResult


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


def _on_collection(mongo_query: MongoQuery) -> Collection:
    """
    Retrieve a MongoDB collection based on the provided query.

    Args:
        mongo_query (MongoQuery): The query object containing database and collection information.

    Returns:
        Collection: The MongoDB collection.
    """
    return _get_mongo_client().get_database(mongo_query.database).get_collection(mongo_query.collection)


def mongo_insert_many(mongo_query: MongoQuery) -> InsertManyResult:
    """
    Insert multiple documents into a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the documents to insert.

    Returns:
        InsertManyResult: The result of the insert operation.
    """
    return _on_collection(mongo_query).insert_many(mongo_query.get_query_model_dump())


def mongo_update_many(mongo_query: MongoQuery) -> UpdateResult:
    """
    Update multiple documents in a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the update criteria and update data.

    Returns:
        UpdateResult: The result of the update operation.
    """
    return _on_collection(mongo_query).update_many(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_update_one(mongo_query: MongoQuery) -> UpdateResult:
    """
    Update a single document in a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the update criteria and update data.

    Returns:
        UpdateResult: The result of the update operation.
    """
    return _on_collection(mongo_query).update_one(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_delete_one(mongo_query: MongoQuery) -> DeleteResult:
    """
    Delete a single document from a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the delete criteria.

    Returns:
        DeleteResult: The result of the delete operation.
    """
    return _on_collection(mongo_query).delete_one(mongo_query.get_query_model_dump())


def mongo_find(mongo_query: MongoQuery) -> FindResult:
    """
    Find multiple documents in a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the find criteria.

    Returns:
        FindResult: A list of documents matching the find criteria.
    """
    return list(_on_collection(mongo_query).find(mongo_query.get_query_model_dump()))


def mongo_find_one(mongo_query: MongoQuery) -> FindOneResult:
    """
    Find a single document in a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the find criteria.

    Returns:
        FindOneResult: A single document matching the find criteria, or None if no document matches.
    """
    return _on_collection(mongo_query).find_one(mongo_query.get_query_model_dump())


def mongo_find_one_and_update(mongo_query: MongoQuery) -> FindOneResult:
    """
    Find a single document and update it in a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the find criteria and update data.

    Returns:
        FindOneResult: The updated document, or None if no document matches.
    """
    return _on_collection(mongo_query).find_one_and_update(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_find_one_and_delete(mongo_query: MongoQuery) -> FindOneResult:
    """
    Find a single document and delete it from a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the find criteria.

    Returns:
        Dict[str, Any]: The deleted document, or None if no document matches.
    """
    return _on_collection(mongo_query).find_one_and_delete(mongo_query.get_query_model_dump())


def mongo_delete_many(mongo_query: MongoQuery) -> DeleteResult:
    """
    Delete multiple documents from a MongoDB collection.

    Args:
        mongo_query (MongoQuery): The query object containing the delete criteria.

    Returns:
        DeleteResult: The result of the delete operation.
    """
    return _on_collection(mongo_query).delete_many(mongo_query.get_query_model_dump())