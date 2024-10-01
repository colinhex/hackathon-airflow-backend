from datetime import datetime
from functools import reduce
from hashlib import md5
from typing import Dict, Optional, List, Set, Tuple, Any, Annotated

from pydantic import Field, BaseModel, AnyUrl, field_validator, Tag, Discriminator, ConfigDict
from typing_extensions import Union, Literal

from unibas.common.model.model_annotations import MongoDatetime, MongoAnyUrl
from unibas.common.model.model_mongo import MongoModel
from unibas.common.model.model_resource import WebContent, WebResource


# #################################################################################################
# GENERIC  ----------------------------------------------------------------------------------------

class ParsedContent(WebContent):
    """
    Model representing parsed web content with text chunks.
    """
    resource_type: Literal['parsed_web_content'] = Field(default='parsed_web_content', frozen=True)
    content: List[str] = Field(default_factory=list, alias="text_chunks")
    embeddings: List[List[float]] = Field(default_factory=list, alias="embeddings")
    features: List[Dict[str, Any]] = Field(default_factory=list, alias="features")


# GENERIC -----------------------------------------------------------------------------------------
# #################################################################################################
# XML PARSED --------------------------------------------------------------------------------------

class ParsedSitemap(ParsedContent):
    """
    Model representing parsed web content for an XML sitemap.

    Attributes:
        resource_type (Literal['parsed_web_content_xml_sitemap']): The type of the resource.
        content (List[WebResource]): List of web resources parsed from the XML sitemap.
    """
    resource_type: Literal['parsed_sitemap'] = Field(default='parsed_sitemap', frozen=True)
    content: List[WebResource] = Field(default_factory=list, alias="content")
    filter_paths: Optional[List[str]] = Field(None, alias="filter")
    modified_after: Optional[MongoDatetime] = Field(None, alias="filter")
    modified_before: Optional[MongoDatetime] = Field(None, alias="filter")


# XML PARSED --------------------------------------------------------------------------------------
# #################################################################################################
# HTML PARSED -------------------------------------------------------------------------------------


class ParsedHtml(ParsedContent):
    resource_type: Literal['parsed_html'] = Field(default='parsed_html', frozen=True)
    attributes: 'HtmlAttributes' = Field(..., alias="attributes")


class HtmlAttributes(BaseModel):
    attribute_type: Literal['html_attributes'] = Field(default='html_attributes', frozen=True)
    title: Optional[str] = Field(None, alias="title")
    author: Optional[str] = Field(None, alias="author")
    date: Optional[str] = Field(None, alias="date")
    description: Optional[str] = Field(None, alias="description")
    keywords: Optional[str] = Field(None, alias="keywords")
    links: Optional['UrlParseResult'] = Field(None, alias="links")


def _url_arche_key(origin: AnyUrl, target: AnyUrl) -> str:
    return md5(string=bytes(f'{origin}:{target}', 'utf-8'), usedforsecurity=False).hexdigest()


class UrlArche(BaseModel):
    origin: MongoAnyUrl = Field(..., alias="origin")
    target: MongoAnyUrl = Field(..., alias="target")
    weight: Optional[float] = Field(0.0, alias="weight")
    key: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        _existing_key = data.get('key')
        self.key = _existing_key or _url_arche_key(self.origin, self.target)

    @field_validator('key')
    def key_computed(cls, value):
        if value is None:
            raise ValueError('key is required')

    def get_key(self) -> str:
        return self.key

    def merge(self, arche: 'UrlArche'):
        self.weight += arche.weight


class UrlGraph(MongoModel):
    name: str
    nodes: Dict[MongoAnyUrl, Optional[MongoDatetime]] = Field(default_factory=dict)
    arches: Dict[str, UrlArche] = Field(default_factory=dict)

    def merge_node(self, node):
        if node not in self.nodes:
            self.nodes[node] = None

    def merge_nodes(self, nodes: Dict[MongoAnyUrl, Optional[MongoDatetime]]):
        for node, value in nodes.items():
            if node not in self.nodes:
                self.nodes[node] = value
            elif value is not None and self.nodes[node] is None:
                self.nodes[node] = value
            elif value is not None and self.nodes[node] is not None:
                self.nodes[node] = max(self.nodes[node], value)

    def merge_arche(self, arche):
        if arche.key in self.arches:
            self.arches[arche.key].merge(arche)
        else:
            self.arches[arche.key] = arche

    def add_arche(self, arche: UrlArche):
        self.merge_node(arche.origin)
        self.merge_node(arche.target)
        self.merge_arche(arche)

    def merge(self, graph: 'UrlGraph'):
        self.merge_nodes(graph.nodes)
        for arche in graph.arches.values():
            self.merge_arche(arche)

    @staticmethod
    def merge_all(graphs: List['UrlGraph']) -> 'UrlGraph':
        return reduce(lambda g1, g2: (g1.merge(g2), g1)[1], graphs, UrlGraph(name=graphs[0].name))

    def get_outgoing_arches(self, origin: AnyUrl) -> List[UrlArche]:
        if origin not in self.nodes:
            return []
        keys = [_url_arche_key(origin, target) for target in self.nodes if target != origin]
        return [self.arches[key] for key in keys if key in self.arches]

    def get_incoming_arches(self, target: AnyUrl) -> List[UrlArche]:
        if target not in self.nodes:
            return []
        keys = [_url_arche_key(origin, target) for origin in self.nodes if origin != target]
        return [self.arches[key] for key in keys if key in self.arches]

    def get_all_arches_for(self, url: AnyUrl) -> List[UrlArche]:
        return self.get_outgoing_arches(url) + self.get_incoming_arches(url)


class UrlParseResult(MongoModel):
    origin: MongoAnyUrl = Field()
    urls: List[Tuple[MongoAnyUrl, int]] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.urls) == 0

    def get_urls(self) -> List[AnyUrl]:
        return [url for url, _ in self.urls]

    def get_urls_with_freq(self) -> List[Tuple[AnyUrl, int]]:
        return self.urls

    def get_origin(self) -> AnyUrl:
        return self.origin

    def get_urls_from_same_host_from_origin(self) -> List[AnyUrl]:
        return list(filter(lambda url: self.origin.host == url.host, self.get_urls()))

    def get_urls_from_different_host_from_origin(self) -> List[AnyUrl]:
        return list(filter(lambda url: self.origin.host != url.host, self.get_urls()))

    def get_graph_data(self, graph_name: str) -> UrlGraph:
        graph = UrlGraph(name=graph_name)
        for url, freq in self.urls:
            graph.add_arche(UrlArche(origin=self.origin, target=url, weight=freq))
        return graph


# HTML PARSED -------------------------------------------------------------------------------------
# #################################################################################################
# PDF PARSED --------------------------------------------------------------------------------------

class ParsedPdf(ParsedContent):
    resource_type: Literal['parsed_pdf'] = Field(default='parsed_pdf', frozen=True)
    attributes: 'PdfAttributes' = Field(..., alias="attributes")


class PdfAttributes(BaseModel):
    attribute_type: Literal['pdf_attributes'] = Field(default='pdf_attributes', frozen=True)
    title: Optional[str] = Field(None, alias="title")
    author: Optional[str] = Field(None, alias="author")
    date: Optional[str] = Field(None, alias="date")
    description: Optional[str] = Field(None, alias="description")
    keywords: Optional[str] = Field(None, alias="keywords")


# PDF PARSED --------------------------------------------------------------------------------------
# #################################################################################################
# DOCUMENT CHUNKS ---------------------------------------------------------------------------------


def attribute_discriminator(v):
    if isinstance(v, list):
        return [attribute_discriminator(vx) for vx in v]
    elif isinstance(v, dict):
        return v.get('attribute_type')
    return getattr(v, 'attribute_type', None)


class DocumentMetadata(BaseModel):
    created_at: MongoDatetime = Field(default_factory=datetime.now, frozen=True)
    lastmod: MongoDatetime
    document_id: str
    attributes: Union[
        Annotated[HtmlAttributes, Tag('html_attributes')],
        Annotated[PdfAttributes, Tag('pdf_attributes')],
    ] = Field(discriminator=Discriminator(attribute_discriminator))
    chunk_id: str
    chunk_index: int


class DocumentChunk(MongoModel):
    model_config = ConfigDict(**MongoModel.model_config)
    resource_type: Literal['document_chunk'] = Field(default='document_chunk', frozen=True)
    text: str
    embedding: List[float]
    tags: Dict[str, Any]
    metadata: DocumentMetadata


# DOCUMENT CHUNKS ---------------------------------------------------------------------------------
# #################################################################################################
# TYPE DEF ----------------------------------------------------------------------------------------

ParsedContentUnion = Union[
    ParsedContent,
    ParsedHtml,
    ParsedPdf,
    ParsedSitemap,
]

# TYPE DEF ----------------------------------------------------------------------------------------
# #################################################################################################
