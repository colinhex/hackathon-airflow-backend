from datetime import datetime
from typing import Union, List

from pydantic import Tag, Field, Discriminator
from typing_extensions import Annotated

from unibas.common.model.model_mongo import MongoModel
from unibas.common.model.model_resource import WebResource, ApiResource, ResourceVariables
from unibas.common.environment.variables import ModelDumpVariables


def resource_discriminator(v):
    """
    Discriminator function to determine the type of resource.

    Args:
        v: The resource to be discriminated, can be a list, dict, or an object.

    Returns:
        The type of the resource as a string.
    """
    if isinstance(v, list):
        return [resource_discriminator(vx) for vx in v]
    elif isinstance(v, dict):
        return v.get(ResourceVariables.RESOURCE_TYPE_FIELD)
    return getattr(v, ResourceVariables.RESOURCE_TYPE_FIELD, None)


class Job(MongoModel):
    """
    Job model representing a job with various resources.

    Attributes:
        created_at (datetime): The timestamp when the job was created.
        processing (bool): Flag indicating if the job is currently being processed.
        tries (int): The number of attempts made to process the job.
        resources (List[Union[WebResource, ApiResource]]): List of resources associated with the job.
    """
    created_at: datetime = Field(default_factory=datetime.now, frozen=True)
    processing: bool = Field(default=False)
    tries: int = Field(default=0)
    resources: List[Union[
        Annotated[WebResource, Tag('web_resource')],
        Annotated[ApiResource, Tag('api_resource')],
        # Define more resource types here.
    ]] = Field(discriminator=Discriminator(resource_discriminator))

    def model_dump(self, **kwargs):
        """
        Dumps the model to a dictionary.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The dictionary representation of the model.
        """
        stringify_datetime: bool = kwargs.pop(ModelDumpVariables.STRINGIFY_DATETIME, False)
        dictionary_dump = super().model_dump(**kwargs)
        if stringify_datetime:
            dictionary_dump['created_at'] = dictionary_dump['created_at'].isoformat()
        return dictionary_dump