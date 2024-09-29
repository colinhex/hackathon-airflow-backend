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

