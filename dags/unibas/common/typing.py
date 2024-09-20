import re
from datetime import datetime
from typing import Any, List, Dict, ClassVar, Tuple, AsyncGenerator, NamedTuple

from bson import ObjectId
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field, root_validator, model_validator

from unibas.common.web.mime_types import TEXT_HTML, TEXT_XML

# Type Aliases

Index = int
HttpCode = int
Feature = float

ConnectionId = str
EmbeddingModel = str
LlmModel = str
Text = str
Tag = str
Key = str

Query: Dict[Key, Any]
Update: Dict[Key, Any]
OpenAiTool = Dict[Key, Any]
TaggingFunction = OpenAiTool

Texts = List[Text]
Tags = List[Tag]
Embedding = List[Feature]
OpenAiTools = List[OpenAiTool]

Messages = List[Dict[Key, Text]]


class AsyncChatCompletion(NamedTuple):
    index: int
    completion: ChatCompletion


Indexed = Dict[Index, Any]
IndexedEmbeddings = Dict[Index, Embedding]
IndexedTexts = Dict[Index, Text]
IndexedTags = Dict[Index, Tags]
IndexedCompletion = Dict[Index, ChatCompletion]

NestedIndexed = Dict[Index, Dict[Index, Any]]
NestedIndexedEmbeddings = Dict[Index, IndexedEmbeddings]
NestedIndexedTexts = Dict[Index, IndexedTexts]
NestedIndexedTags = Dict[Index, IndexedTags]

NestedIndexes = List[NestedIndexed]

FlattenedIndex = List[Tuple[Index, Any]]

AsyncChatCompletions = AsyncGenerator[List[AsyncChatCompletion], None]


# Timestamps
class IsoTime(BaseModel):
    iso_time_pattern: ClassVar[re.Pattern] = re.compile(
        r'^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-][01]\d:[0-5]\d)?$'
    )

    time: str | None = None

    def __init__(self, time=None):
        super(IsoTime, self).__init__()
        self.time = time
        self.verify()

    def verify(self):
        if self.time is None:
            return
        match = self.iso_time_pattern.match(self.time)
        if not match:
            raise ValueError(f'Couldn\'t parse ISO time {self.time} with pattern {self.iso_time_pattern}')

    def to_datetime(self) -> datetime | None:
        self.verify()
        if self.time is None:
            return None
        return datetime.fromisoformat(self.time)

    def timestamp(self) -> str | None:
        self.verify()
        return self.time


# Resources

class WebResource(BaseModel):
    loc: str
    lastmod: str | None = None
    mime_type: str | None = None

    @staticmethod
    def from_serialised(web_resource: Dict[str, Any]) -> 'WebResource':
        return WebResource(**web_resource)

    @staticmethod
    def from_serialised_list(web_resources: List[Dict[str, Any]]) -> List['WebResource']:
        return [WebResource(**web_resource) for web_resource in web_resources]


class SitemapResource(WebResource):
    mime_type: str = TEXT_XML

    @staticmethod
    def from_serialised(web_resource: Dict[str, Any]) -> 'SitemapResource':
        return SitemapResource(**web_resource)

    @staticmethod
    def from_serialised_list(web_resources: List[Dict[str, Any]]) -> List['SitemapResource']:
        return [SitemapResource(**web_resource) for web_resource in web_resources]


class HtmlResource(WebResource):
    mime_type: str = TEXT_HTML

    @staticmethod
    def from_serialised(web_resource: Dict[str, Any]) -> 'HtmlResource':
        return HtmlResource(**web_resource)

    @staticmethod
    def from_serialised_list(web_resources: List[Dict[str, Any]]) -> List['HtmlResource']:
        return [HtmlResource(**web_resource) for web_resource in web_resources]


# Batches

class Batch(BaseModel):
    dag_id: str | None = None
    mime_type: str
    batch_size: int
    tries: int = 0
    processing: bool = False
    resources: List[Dict[str, Any]] = []


class MongoHtmlBatch(Batch):
    id: str = Field(default_factory=str)
    resources: List[HtmlResource] = []

    def get_object_id(self):
        return self.id

    @model_validator(mode='before')
    def handle_id_fields(cls, values):
        # Check for either '_id' or 'id' in the input data
        if '_id' in values and isinstance(values['_id'], str):
            values['id'] = MongoHtmlBatch.try_id_conversion(values['_id'])
        elif 'id' in values and isinstance(values['id'], str):
            values['id'] = MongoHtmlBatch.try_id_conversion(values['id'])
        return values

    @staticmethod
    def try_id_conversion(_id: str) -> str:
        try:
            return str(ObjectId(_id))
        except Exception as e:
            raise ValueError(f'Could not convert to objectId, invalid _id string: {_id}, {e}')

    @staticmethod
    def from_serialised(batch: Dict[str, Any]) -> 'MongoHtmlBatch':
        return MongoHtmlBatch(**batch)

    @staticmethod
    def from_serialised_list(batches: List[Dict[str, Any]]) -> List['MongoHtmlBatch']:
        return [MongoHtmlBatch(**batch) for batch in batches]


# WebClients

class WebClientResponse(BaseModel):
    loc: str
    code: int
    content_type: str
    charset: str
    lastmod: IsoTime
    extracted_at: IsoTime
    content_encoding: str | None = None
    content: Any | None = None

    @staticmethod
    def from_serialised(web_client_response: Dict[str, Any]) -> 'WebClientResponse':
        return WebClientResponse(**web_client_response)

    @staticmethod
    def from_serialised_list(web_client_responses: List[Dict[str, Any]]) -> List['WebClientResponse']:
        return [WebClientResponse(**response) for response in web_client_responses]


class ParsedHtml(WebClientResponse):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    keywords: str | None = None
    links: List[Dict[str, Any]] | None = None
    content: str | None = None

    @staticmethod
    def from_serialised(parsed_html: Dict[str, Any]) -> 'ParsedHtml':
        return ParsedHtml(**parsed_html)

    @staticmethod
    def from_serialised_list(parsed_htmls: List[Dict[str, Any]]) -> List['ParsedHtml']:
        return [ParsedHtml(**response) for response in parsed_htmls]


class CleanedHtml(ParsedHtml):
    @staticmethod
    def from_serialised(cleaned_html: Dict[str, Any]) -> 'CleanedHtml':
        return CleanedHtml(**cleaned_html)

    @staticmethod
    def from_serialised_list(cleaned_htmls: List[Dict[str, Any]]) -> List['CleanedHtml']:
        return [CleanedHtml(**response) for response in cleaned_htmls]


# Attributes

class HtmlAttributes(BaseModel):
    loc: str
    author: str | None = None
    description: str | None = None
    keywords: str | None = None
    lastmod: str | None = None

    @staticmethod
    def from_serialised(html_attributes: Dict[str, Any]) -> 'HtmlAttributes':
        return HtmlAttributes(**html_attributes)

    @staticmethod
    def from_serialised_list(html_attributes: List[Dict[str, Any]]) -> List['HtmlAttributes']:
        return [HtmlAttributes(**response) for response in html_attributes]


# Documents

class HtmlDocument(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    text: str
    embedding: List[float]
    tags: List[str]
    attributes: HtmlAttributes

    @staticmethod
    def from_serialised(html_document: Dict[str, Any]) -> 'HtmlDocument':
        return HtmlDocument(**html_document)

    @staticmethod
    def from_serialised_list(html_documents: List[Dict[str, Any]]) -> List['HtmlDocument']:
        return [HtmlDocument(**response) for response in html_documents]


# Queries

class SitemapQuery(BaseModel):
    sitemap_url: str
    start_paths: List[str] = []
    default_mod_after: IsoTime = IsoTime(time=datetime(2024, 1, 1).isoformat())
    mod_after: IsoTime


class MongoQuery(BaseModel):
    database: str
    collection: str
    query: Dict[str, Any] | List[Dict[str, Any]] | None = None
    update: Dict[str, Any] | None = None


def all_to_dict(list_of_serializable: List[Any]) -> List[Dict[str, Any]]:
    return [data.dict() for data in list_of_serializable]

