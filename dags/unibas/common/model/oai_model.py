from typing import Dict

from pydantic import BaseModel, Field
from typing_extensions import List

from unibas.common.constants import OpenAi
from unibas.common.model.prompt_model import create_feature_extraction_messages


class OpenAiEmbedding(BaseModel):
    embedding_model: str = Field(OpenAi.embedding_model, alias='embedding_model')
    chunk_index: int
    text_chunk: str
    embedding: List[float] = Field(default_factory=list)


class OpenAiEmbeddings(BaseModel):
    embedding_model: str = Field(OpenAi.embedding_model, alias='embedding_model')
    embeddings: List[OpenAiEmbedding] = Field(default_factory=list)

    def get_ordered_text_chunks(self) -> List[str]:
        return list(map(lambda q: q.text_chunk, sorted(self.embeddings, key=lambda e: e.chunk_index)))


class OpenAiBatchCompletionEntryBody(BaseModel):
    model: str = Field(OpenAi.embedding_model, alias='embedding_model')
    messages: List[Dict[str, str]]
    max_tokens: int = Field(1000, alias='max_tokens')


class OpenAiBatchCompletionEntry(BaseModel):
    custom_id: str
    method: str = Field('POST', frozen=True)
    url: str = Field('/v1/chat/completions', frozen=True)
    body: OpenAiBatchCompletionEntryBody = Field(default_factory=dict)

    @staticmethod
    def create_from_text_chunk(chunk_index: int, text_chunk: str) -> 'OpenAiBatchCompletionEntry':
        body = OpenAiBatchCompletionEntryBody(messages=create_feature_extraction_messages(text_chunk))
        return OpenAiBatchCompletionEntry(custom_id=str(chunk_index), body=body)


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

