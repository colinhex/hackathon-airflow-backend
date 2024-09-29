from datetime import datetime
from typing import Annotated, Any, Dict, List

from bson import ObjectId
from pydantic import AfterValidator, PlainSerializer, AnyUrl, AnyHttpUrl


def object_id_validate(v: ObjectId) -> ObjectId:
    assert ObjectId.is_valid(v), f'{v} is not a valid ObjectId'
    if isinstance(v, str):
        return ObjectId(v)
    return v


def object_id_json_serialize(v: ObjectId) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    else:
        raise ValueError(f'Expecting ObjectId or str, got {type(v)}')


# Annotated type for MongoDB ObjectId with validation and serialization
MongoObjectId = Annotated[
    ObjectId | str,
    AfterValidator(object_id_validate),
    PlainSerializer(object_id_json_serialize, when_used='json')
]


def datetime_validate(v: datetime | str) -> datetime:
    if isinstance(v, str):
        return datetime.fromisoformat(v)
    return v


def datetime_json_serialize(v: datetime) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    else:
        raise ValueError(f'Expecting datetime or str, got {type(v)}')


MongoDatetime = Annotated[
    datetime,
    AfterValidator(datetime_validate),
    PlainSerializer(datetime_json_serialize, when_used='json')
]


MongoAnyUrl = Annotated[
    AnyUrl,
    PlainSerializer(lambda v: str(v), when_used='unless-none')
]


MongoAnyHttpUrl = Annotated[
    AnyHttpUrl,
    AfterValidator(datetime_validate),
    PlainSerializer(lambda v: str(v), when_used='unless-none')
]


def indexed_validate(v: Dict[int, Any] | List[Any]) -> Dict[int, Any]:
    if isinstance(v, list):
        return {k: v for k, v in enumerate(v)}
    return v


def indexed_serialize(v: Dict[int, Any] | List[Any]) -> List[Any]:
    if isinstance(v, dict):
        return [v[k] for k in sorted(v.keys())]
    return v


Indexed = Annotated[Dict[int, Any] | List[Any], PlainSerializer(indexed_serialize, when_used='always')]

