from typing import Dict

from pydantic import BaseModel, Field
from typing_extensions import List

from unibas.common.environment import OpenAiEnvVariables
from unibas.common.model.model_prompt import create_feature_extraction_messages


class OpenAiEmbedding(BaseModel):
    embedding_model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    chunk_index: int
    text_chunk: str
    embedding: List[float] = Field(default_factory=list)


class OpenAiEmbeddings(BaseModel):
    embedding_model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    embeddings: Dict[int, OpenAiEmbedding] = Field(default_factory=list)

    def add_text_chunk(self, chunk_index: int, text_chunk: str):
        if chunk_index in self.embeddings:
            raise ValueError(f'Text chunk already exists for chunk_index {chunk_index}')
        self.embeddings[chunk_index] = OpenAiEmbedding(chunk_index=chunk_index, text_chunk=text_chunk)

    def add_embedding(self, chunk_index: int, embedding: List[float]):
        if chunk_index not in self.embeddings:
            raise ValueError(f'No text_chunk found for chunk_index {chunk_index}')
        self.embeddings[chunk_index].embedding = embedding

    def get_embedding(self, chunk_index: int) -> List[float]:
        if chunk_index not in self.embeddings:
            raise ValueError(f'No text_chunk found for chunk_index {chunk_index}')
        return self.embeddings[chunk_index].embedding

    def get_text_chunk(self, chunk_index: int) -> str:
        if chunk_index not in self.embeddings:
            raise ValueError(f'No text_chunk found for chunk_index {chunk_index}')
        return self.embeddings[chunk_index].text_chunk

    def get_ordered_text_chunks(self) -> List[str]:
        return list(map(lambda q: q.text_chunk, sorted(self.embeddings, key=lambda e: e.chunk_index)))


class OpenAiBatchCompletionEntryBody(BaseModel):
    model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    messages: List[Dict[str, str]]
    max_tokens: int = Field(1000, alias='max_tokens')


class OpenAiBatchCompletionEntry(BaseModel):
    custom_id: str
    method: str = Field('POST', frozen=True)
    url: str = Field('/v1/chat/completions', frozen=True)
    body: OpenAiBatchCompletionEntryBody = Field(default_factory=dict)

    @staticmethod
    def create_from_text_chunk(chunk_index: int, text_chunk: str, message_generator) -> 'OpenAiBatchCompletionEntry':
        body = OpenAiBatchCompletionEntryBody(messages=message_generator(text_chunk))
        return OpenAiBatchCompletionEntry(custom_id=str(chunk_index), body=body)


class OpenAiBatchCompletionEntries(BaseModel):
    entries: Dict[int, OpenAiBatchCompletionEntry] = Field(default_factory=dict)

    def add(self, chunk_index: int, text_chunk: str, message_generator):
        self.entries[chunk_index] = OpenAiBatchCompletionEntry.create_from_text_chunk(chunk_index, text_chunk, message_generator)

    def to_batch_file_str(self):
        return '\n'.join([e.model_dump_json() for e in self.entries.values()])

    def to_batch_file(self) -> bytes:
        return '\n'.join([e.model_dump_json() for e in self.entries.values()]).encode('utf-8')


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

