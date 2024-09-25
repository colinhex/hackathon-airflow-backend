from airflow.providers.mongo.hooks.mongo import MongoHook
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.results import InsertManyResult, UpdateResult, DeleteResult
from typing_extensions import Dict, Any, List, Optional

from unibas.common.environment import MongoAtlasEnvVariables, TestEnvVariables
from unibas.common.model.model_mongo import MongoQuery

FindResult = List[Dict[str, Any]]
FindOneResult = Optional[Dict[str, Any]]


def _get_mongo_client() -> MongoClient:
    test_conn_string = TestEnvVariables.atlas_conn_string
    if test_conn_string is not None:
        return MongoClient(test_conn_string)
    return MongoHook(conn_id=MongoAtlasEnvVariables.conn_id).get_conn()


def _on_collection(mongo_query: MongoQuery) -> Collection:
    return _get_mongo_client().get_database(mongo_query.database).get_collection(mongo_query.collection)


def mongo_insert_many(mongo_query: MongoQuery) -> InsertManyResult:
    return _on_collection(mongo_query).insert_many(mongo_query.get_query_model_dump())


def mongo_update_many(mongo_query: MongoQuery) -> UpdateResult:
    return _on_collection(mongo_query).update_many(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_update_one(mongo_query: MongoQuery) -> UpdateResult:
    return _on_collection(mongo_query).update_one(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_delete_one(mongo_query: MongoQuery) -> DeleteResult:
    return _on_collection(mongo_query).delete_one(mongo_query.get_query_model_dump())


def mongo_find(mongo_query: MongoQuery) -> FindResult:
    return list(_on_collection(mongo_query).find(mongo_query.get_query_model_dump()))


def mongo_find_one(mongo_query: MongoQuery) -> FindOneResult:
    return _on_collection(mongo_query).find_one(mongo_query.get_query_model_dump())


def mongo_find_one_and_update(mongo_query: MongoQuery) -> FindOneResult:
    return _on_collection(mongo_query).find_one_and_update(mongo_query.get_query_model_dump(), mongo_query.get_update_model_dump())


def mongo_find_one_and_delete(mongo_query: MongoQuery) -> Dict[str, Any]:
    return _on_collection(mongo_query).find_one_and_delete(mongo_query.get_query_model_dump() )


def mongo_delete_many(mongo_query: MongoQuery) -> DeleteResult:
    return _on_collection(mongo_query).delete_many(mongo_query.get_query_model_dump())
