from typing import Dict, Optional

from pydantic import BaseModel, Field
from typing_extensions import List

from unibas.common.environment.variables import OpenAiEnvVariables
from unibas.common.model.model_job import Job
from unibas.common.model.model_parsed import ParsedWebContentTextChunks


class OpenAiEmbedding(BaseModel):
    embedding_model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    resource_id: str
    chunk_index: int
    embedding_index: int
    text_chunk: str
    embedding: List[float] = Field(default_factory=list)


class OpenAiEmbeddings(BaseModel):
    embedding_model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    embeddings: List[OpenAiEmbedding] = Field(default_factory=list)

    def add_job(self, job: Job):
        for resource in job.resources:
            assert isinstance(resource, ParsedWebContentTextChunks)
            for chunk_index, text_chunk in enumerate(resource.content):
                self.add_request(resource_id=str(resource.id), chunk_index=chunk_index, text_chunk=text_chunk)

    def add_request(self, resource_id: str, chunk_index: int, text_chunk: str):
        self.embeddings.append(OpenAiEmbedding(
            resource_id=resource_id,
            chunk_index=chunk_index,
            embedding_index=len(self.embeddings),
            text_chunk=text_chunk
        ))

    def add_embedding(self, embedding_index: int, embedding: List[float]):
        self.embeddings[embedding_index].embedding = embedding

    def get_ordered_embeddings(self, resource_id: str) -> List[List[float]]:
        """
        Get the embeddings ordered by their chunk index.

        Returns:
            List[List[float]]: The ordered list of embeddings.
        """
        return list(
            map(
                lambda q: q.embedding,
                sorted(
                    filter(
                        lambda e: e.resource_id == resource_id,
                        self.embeddings
                    ),
                    key=lambda e: e.chunk_index)
            )
        )

    def get_ordered_text_chunks(self) -> List[str]:
        """
        Get the text chunks ordered by their chunk index.

        Returns:
            List[str]: The ordered list of text chunks.
        """
        return list(map(lambda q: q.text_chunk, sorted(self.embeddings, key=lambda e: e.embedding_index)))


class OpenAiFeatureResponse(BaseModel):
    """
    Model representing a feature response from OpenAI.

    Attributes:
        intended_audience (List[str]): The list of intended audiences.
        departments (List[str]): The list of departments.
        faculties (List[str]): The list of faculties.
        administrative_services (List[str]): The list of administrative services.
        degree_levels (List[str]): The list of degree levels.
        topics (List[str]): The list of topics.
        information_type (List[str]): The list of information types.
        keywords (List[str]): The list of keywords.
        entities_mentioned (List[str]): The list of entities mentioned.
    """
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


class OpenAiFeatures(BaseModel):
    llm_model: str = Field(OpenAiEnvVariables.llm_model, alias='llm_model')
    features: List[OpenAiFeature] = Field(default_factory=list)

    def add_job(self, job: Job):
        for resource in job.resources:
            assert isinstance(resource, ParsedWebContentTextChunks)
            for chunk_index, text_chunk in enumerate(resource.content):
                feature = OpenAiFeatureResponse(**resource.features[chunk_index]) if len(resource.features) > chunk_index else None
                self.features.append(OpenAiFeature(
                    resource_id=str(resource.id),
                    chunk_index=chunk_index,
                    embedding_index=len(self.features),
                    text_chunk=text_chunk,
                    feature=feature
                ))

    def add_response(self, feature_index: int, feature: OpenAiFeatureResponse):
        self.features[feature_index].feature = feature

    def get_ordered_features(self, resource_id: str) -> List[OpenAiFeatureResponse]:
        """
        Get the embeddings ordered by their chunk index.

        Returns:
            List[List[float]]: The ordered list of embeddings.
        """
        return list(
            map(
                lambda q: q.feature,
                sorted(
                    filter(
                        lambda e: e.resource_id == resource_id,
                        self.features
                    ),
                    key=lambda e: e.chunk_index)
            )
        )

    def get_ordered_text_chunks(self) -> List[str]:
        """
        Get the text chunks ordered by their chunk index.

        Returns:
            List[str]: The ordered list of text chunks.
        """
        return list(map(lambda q: q.text_chunk, sorted(self.features, key=lambda e: e.embedding_index)))


class OpenAiBatchCompletionEntryBody(BaseModel):
    """
    Model representing the body of a batch completion entry.

    Attributes:
        model (str): The model used for embedding.
        messages (List[Dict[str, str]]): The list of messages.
        max_tokens (int): The maximum number of tokens.
    """
    model: str = Field(OpenAiEnvVariables.embedding_model, alias='embedding_model')
    messages: List[Dict[str, str]]
    max_tokens: int = Field(1000, alias='max_tokens')


class OpenAiBatchCompletionEntry(BaseModel):
    """
    Model representing a batch completion entry.

    Attributes:
        custom_id (str): The custom identifier for the entry.
        method (str): The HTTP method for the entry.
        url (str): The URL for the entry.
        body (OpenAiBatchCompletionEntryBody): The body of the entry.
    """
    custom_id: str
    method: str = Field('POST', frozen=True)
    url: str = Field('/v1/chat/completions', frozen=True)
    body: OpenAiBatchCompletionEntryBody = Field(default_factory=dict)

    @staticmethod
    def create_from_text_chunk(chunk_index: int, text_chunk: str, message_generator) -> 'OpenAiBatchCompletionEntry':
        """
        Create a batch completion entry from a text chunk.

        Args:
            chunk_index (int): The index of the text chunk.
            text_chunk (str): The text chunk.
            message_generator (Callable): The function to generate messages from the text chunk.

        Returns:
            OpenAiBatchCompletionEntry: The created batch completion entry.
        """
        body = OpenAiBatchCompletionEntryBody(messages=message_generator(text_chunk))
        return OpenAiBatchCompletionEntry(custom_id=str(chunk_index), body=body)


class OpenAiBatchCompletionEntries(BaseModel):
    """
    Model representing a collection of batch completion entries.

    Attributes:
        entries (Dict[int, OpenAiBatchCompletionEntry]): A dictionary of batch completion entries indexed by chunk index.
    """
    entries: Dict[int, OpenAiBatchCompletionEntry] = Field(default_factory=dict)

    def add(self, chunk_index: int, text_chunk: str, message_generator):
        """
        Add a batch completion entry to the collection.

        Args:
            chunk_index (int): The index of the text chunk.
            text_chunk (str): The text chunk.
            message_generator (Callable): The function to generate messages from the text chunk.
        """
        self.entries[chunk_index] = OpenAiBatchCompletionEntry.create_from_text_chunk(chunk_index, text_chunk, message_generator)

    def to_batch_file_str(self) -> str:
        """
        Convert the batch completion entries to a string.

        Returns:
            str: The string representation of the batch completion entries.
        """
        return '\n'.join([e.model_dump_json() for e in self.entries.values()])


