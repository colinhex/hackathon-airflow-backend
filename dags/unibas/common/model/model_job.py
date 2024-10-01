from datetime import datetime
from typing import Union, List

from unibas.common.model.model_parsed import *
from unibas.common.model.model_resource import *


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
        return v.get("resource_type")
    return getattr(v, "resource_type", None)


class Job(MongoModel):
    """
    Job model representing a job with various resources.

    Attributes:
        created_at (datetime): The timestamp when the job was created.
        processing (bool): Flag indicating if the job is currently being processed.
        tries (int): The number of attempts made to process the job.
        resources (List[Union[WebResource, ApiResource]]): List of resources associated with the job.
    """
    created_by: str
    created_at: MongoDatetime = Field(default_factory=datetime.now, frozen=True)
    processing: bool = Field(default=False)
    tries: int = Field(default=0)
    resources: List[Union[
        Annotated[ApiResource, Tag('api_resource')],
        Annotated[WebResource, Tag('web_resource')],
        Annotated[WebContentHeader, Tag('web_content_header')],
        Annotated[WebContent, Tag('web_content')],
        Annotated[ParsedPdf, Tag('parsed_pdf')],
        Annotated[ParsedHtml, Tag('parsed_html')],
        Annotated[DocumentChunk, Tag('document_chunk')],
    ]] = Field(discriminator=Discriminator(resource_discriminator))

