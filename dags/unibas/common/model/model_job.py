from datetime import datetime
from typing import Union, List

from pydantic import Tag, Field, Discriminator
from typing_extensions import Annotated

from unibas.common.model.model_mongo import MongoModel
from unibas.common.model.model_resource import WebResource, ApiResource, ResourceVariables
from unibas.common.environment import ModelDumpVariables


def resource_discriminator(v):
    if isinstance(v, list):
        return [resource_discriminator(vx) for vx in v]
    elif isinstance(v, dict):
        return v.get(ResourceVariables.RESOURCE_TYPE_FIELD)
    return getattr(v, ResourceVariables.RESOURCE_TYPE_FIELD, None)


class Job(MongoModel):
    created_at: datetime = Field(default_factory=datetime.now, frozen=True)
    processing: bool = Field(default=False)
    tries: int = Field(default=0)
    resources: List[Union[
        Annotated[WebResource, Tag('web_resource')],
        Annotated[ApiResource, Tag('api_resource')],

        # Define more resource types here.

    ]] = Field(discriminator=Discriminator(resource_discriminator))

    def model_dump(self, **kwargs):
        stringify_datetime: bool = kwargs.pop(ModelDumpVariables.STRINGIFY_DATETIME, False)
        dictionary_dump = super().model_dump(**kwargs)
        if stringify_datetime:
            dictionary_dump['created_at'] = dictionary_dump['created_at'].isoformat()
        return dictionary_dump

