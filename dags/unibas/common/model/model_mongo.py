from bson import ObjectId
from pydantic import BaseModel, Field as PydanticField, ConfigDict

from unibas.common.model.model_annotations import MongoObjectId


class MongoModel(BaseModel):
    """
    Base model for MongoDB documents.

    Attributes:
        id (MongoObjectId): The unique identifier for the document.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: MongoObjectId = PydanticField(default_factory=ObjectId, alias='_id')

    @staticmethod
    def dump_all_models(models):
        return [model.model_dump(by_alias=True) for model in models]

    @staticmethod
    def dump_all_models_json(models):
        return [model.model_dump_json(by_alias=True) for model in models]
