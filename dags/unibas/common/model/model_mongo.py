from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, Field as PydanticField, ConfigDict, AfterValidator, PlainSerializer, Field
from typing_extensions import Optional, Union, Any, Dict, List

from unibas.common.environment.variables import ModelDumpVariables
from unibas.common.logic.logic_utility import transform_nested


def object_id_validate(v: ObjectId | str) -> ObjectId:
    assert ObjectId.is_valid(v), f'{v} is not a valid ObjectId'
    if isinstance(v, str):
        return ObjectId(v)
    return v


def object_id_serialize(v: ObjectId) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    else:
        raise ValueError(f'Expecting ObjectId or str, got {type(v)}')


MongoObjectId = Annotated[ObjectId | str, AfterValidator(object_id_validate), PlainSerializer(object_id_serialize)]


class MongoModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: MongoObjectId = PydanticField(default_factory=ObjectId, alias='_id')

    # Methods to write the id as an
    def model_dump_json(self, **kwargs):
        kwargs.setdefault('by_alias', True)
        return super().model_dump_json(**kwargs)

    def model_dump(self, **kwargs):
        """
        Overwritten model dump. Call with custom kwarg STRINGIFY_OBJECT_ID=True when serialising for XComArg
        """
        kwargs.setdefault('by_alias', True)
        stringify_object_id: bool = kwargs.pop(ModelDumpVariables.STRINGIFY_OBJECT_ID, False)
        dump = super().model_dump(**kwargs)
        if not stringify_object_id and '_id' in dump:
            dump['_id'] = ObjectId(dump.pop('_id'))
        return dump


class MongoQuery(BaseModel):
    database: str
    collection: str
    query: 'MongoQueryDefinition' = Field(None, alias='query')
    update: 'MongoUpdateDefinition' = Field(None, alias='query')

    def get_query_model_dump(self):
        return transform_nested(self.query, lambda m: m.model_dump(), MongoModel)

    def get_update_model_dump(self):
        return transform_nested(self.update, lambda m: m.model_dump(), MongoModel)


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
