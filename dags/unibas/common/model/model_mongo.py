from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, Field as PydanticField, ConfigDict, AfterValidator, PlainSerializer, Field
from typing_extensions import Optional, Union, Any, Dict, List

from unibas.common.environment.variables import ModelDumpVariables
from unibas.common.logic.logic_utility import transform_nested


def object_id_validate(v: ObjectId | str) -> ObjectId:
    """
    Validate and convert a value to an ObjectId.

    Args:
        v (ObjectId | str): The value to validate and convert.

    Returns:
        ObjectId: The validated ObjectId.

    Raises:
        AssertionError: If the value is not a valid ObjectId.
    """
    assert ObjectId.is_valid(v), f'{v} is not a valid ObjectId'
    if isinstance(v, str):
        return ObjectId(v)
    return v


def object_id_serialize(v: ObjectId) -> str:
    """
    Serialize an ObjectId to a string.

    Args:
        v (ObjectId): The ObjectId to serialize.

    Returns:
        str: The serialized ObjectId.

    Raises:
        ValueError: If the value is not an ObjectId.
    """
    if isinstance(v, ObjectId):
        return str(v)
    else:
        raise ValueError(f'Expecting ObjectId or str, got {type(v)}')


# Annotated type for MongoDB ObjectId with validation and serialization
MongoObjectId = Annotated[ObjectId | str, AfterValidator(object_id_validate), PlainSerializer(object_id_serialize)]


class MongoModel(BaseModel):
    """
    Base model for MongoDB documents.

    Attributes:
        id (MongoObjectId): The unique identifier for the document.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: MongoObjectId = PydanticField(default_factory=ObjectId, alias='_id')

    def model_dump_json(self, **kwargs):
        """
        Dump the model to a JSON string.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            str: The JSON string representation of the model.
        """
        kwargs.setdefault('by_alias', True)
        return super().model_dump_json(**kwargs)

    def model_dump(self, **kwargs):
        """
        Dump the model to a dictionary.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The dictionary representation of the model.
        """
        kwargs.setdefault('by_alias', True)
        stringify_object_id: bool = kwargs.pop(ModelDumpVariables.STRINGIFY_OBJECT_ID, False)
        dump = super().model_dump(**kwargs)
        if not stringify_object_id and '_id' in dump:
            dump['_id'] = ObjectId(dump.pop('_id'))
        return dump


class MongoQuery(BaseModel):
    """
    Model for MongoDB queries.

    Attributes:
        database (str): The name of the database.
        collection (str): The name of the collection.
        query (MongoQueryDefinition): The query definition.
        update (MongoUpdateDefinition): The update definition.
    """
    database: str
    collection: str
    query: 'MongoQueryDefinition' = Field(None, alias='query')
    update: 'MongoUpdateDefinition' = Field(None, alias='query')

    def get_query_model_dump(self):
        """
        Get the model dump of the query.

        Returns:
            dict: The dictionary representation of the query model.
        """
        return transform_nested(self.query, lambda m: m.model_dump(), MongoModel)

    def get_update_model_dump(self):
        """
        Get the model dump of the update.

        Returns:
            dict: The dictionary representation of the update model.
        """
        return transform_nested(self.update, lambda m: m.model_dump(), MongoModel)


# Type definitions for MongoDB query and update definitions
MongoQueryDefinition = Optional[Union[
    Dict[str, Any],
    List[Union[MongoModel, Dict[str, Any]]],
    MongoModel
]]

MongoUpdateDefinition = Optional[Union[
    Dict[str, Any],
    List[Union[MongoModel, Dict[str, Any]]],
    MongoModel
]]