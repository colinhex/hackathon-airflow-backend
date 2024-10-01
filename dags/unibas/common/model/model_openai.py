from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import List


class OpenAiFeatureResponse(BaseModel):
    intended_audience: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    faculties: List[str] = Field(default_factory=list)
    administrative_services: List[str] = Field(default_factory=list)
    degree_levels: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    information_type: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    entities_mentioned: List[str] = Field(default_factory=list)


class OpenAiFeature(BaseModel):
    resource_id: str
    chunk_index: int
    embedding_index: int
    text_chunk: str
    feature: Optional[OpenAiFeatureResponse] = Field(default=None)


