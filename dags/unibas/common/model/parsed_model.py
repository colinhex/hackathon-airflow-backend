from datetime import datetime
from functools import reduce
from hashlib import md5
from typing import Dict, Optional, List, Set, Tuple

from pydantic import Field, BaseModel, AnyUrl
from typing_extensions import Union, Literal

from unibas.common.model.mongo_model import MongoModel
from unibas.common.model.resource_model import WebContent, WebResource


# #################################################################################################
# GENERIC  ----------------------------------------------------------------------------------------

class ParsedWebContent(WebContent):
    started_parsing_at: Optional[datetime] = Field(None)
    finished_parsing_at: datetime = Field(default_factory=datetime.now)
    parsed_in_seconds: Optional[float] = Field(None)
    resource_type: Literal['parsed_web_content'] = Field(default='parsed_web_content', frozen=True)
    success: bool

    def add_parse_time(self, started_parsing_at: datetime) -> 'ParsedContentUnion':
        self.started_parsing_at = started_parsing_at
        self.parsed_in_seconds = (started_parsing_at - self.finished_parsing_at).total_seconds()
        return self


class ParsedWebContentSuccess(ParsedWebContent):
    success: bool = Field(True, frozen=True)
    resource_type: Literal['parsed_web_content_success'] = Field(default='parsed_web_content_success', frozen=True)


class ParsedWebContentTextChunks(ParsedWebContentSuccess):
    resource_type: Literal['parsed_web_content_text_chunks'] = Field(default='parsed_web_content_text_chunks', frozen=True)
    text_chunks: Dict[int, str] = Field(default_factory=dict, alias="text_chunks")


class ParsedWebContentFailure(ParsedWebContent):
    success: bool = Field(False, frozen=True)
    resource_type: Literal['parsed_web_content_failure'] = Field(default='parsed_web_content_failure', frozen=True)
    implemented: bool = Field(...)
    reason: str = Field(...)

    @classmethod
    def create(cls, content: WebContent, reason: Union[RuntimeError, Exception, str, None]) -> 'ParsedWebContentFailure':
        return ParsedWebContentFailure(
            loc=content.loc,
            lastmod=content.lastmod,
            code=content.code,
            mime_type=content.mime_type,
            charset=content.charset,
            content=content.content,
            implemented=not isinstance(reason, NotImplementedError),
            reason=f'{reason}'
        )


# GENERIC -----------------------------------------------------------------------------------------
# #################################################################################################
# XML PARSED --------------------------------------------------------------------------------------

class ParsedWebContentXmlSitemapResult(ParsedWebContentSuccess):
    resource_type: Literal['parsed_web_content_xml_sitemap'] = Field(default='parsed_web_content_xml_sitemap', frozen=True)
    content: List[WebResource] = Field(default_factory=list, alias="content")


# XML PARSED --------------------------------------------------------------------------------------
# #################################################################################################
# HTML PARSED -------------------------------------------------------------------------------------


class ParsedWebContentHtml(ParsedWebContentTextChunks):
    resource_type: Literal['parsed_web_content_success'] = Field(default='parsed_web_content_html', frozen=True)
    attributes: 'HtmlAttributes' = Field(..., alias="attributes")
    content: 'TextChunks' = Field(default_factory=list, alias="content")


class HtmlAttributes(BaseModel):
    title: Optional[str] = Field(..., alias="title")
    author: Optional[str] = Field(..., alias="author")
    date: Optional[str] = Field(..., alias="date")
    description: Optional[str] = Field(..., alias="description")
    keywords: Optional[str] = Field(..., alias="keywords")
    links: 'UrlParseResult' = Field(..., alias="links")


class UrlArche(BaseModel):
    origin: AnyUrl = Field(..., alias="origin")
    target: AnyUrl = Field(..., alias="target")
    weight: Optional[float] = Field(..., alias="weight")

    def key(self) -> str:
        return md5(string=bytes(f'{self.origin}:{self.target}', 'utf-8')).hexdigest()

    def merge(self, arche: 'UrlArche'):
        self.weight += arche.weight


class UrlGraph(MongoModel):
    nodes: Set[AnyUrl] = Field(default_factory=set)
    arches: Dict[str, UrlArche] = Field(default_factory=dict)

    def add_arche(self, arche: UrlArche):
        self.nodes.add(arche.origin)
        self.nodes.add(arche.target)
        key: str = arche.key()
        if key in self.arches:
            self.arches[key].merge(arche)
        else:
            self.arches[key] = arche

    def merge(self, graph: 'UrlGraph'):
        for arche in graph.arches.values():
            self.add_arche(arche)

    @staticmethod
    def merge_all(graphs: List['UrlGraph']) -> 'UrlGraph':
        return reduce(lambda g1, g2: g1.merge(g2), graphs, UrlGraph())


class UrlParseResult(MongoModel):
    origin: AnyUrl = Field()
    urls: List[Tuple[AnyUrl, int]] = Field(default_factory=list)

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

    def get_graph_data(self) -> UrlGraph:
        graph = UrlGraph()
        for url, freq in self.urls:
            graph.add_arche(UrlArche(origin=self.origin, target=url, weight=freq))
        return graph


# HTML PARSED -------------------------------------------------------------------------------------
# #################################################################################################
# PDF PARSED --------------------------------------------------------------------------------------

class ParsedWebContentPdf(ParsedWebContentTextChunks):
    resource_type: Literal['parsed_web_content_pdf'] = Field(default='parsed_web_content_pdf', frozen=True)
    attributes: 'PdfAttributes' = Field(..., alias="attributes")
    content: 'TextChunks' = Field(default_factory=list, alias="content")


class PdfAttributes(BaseModel):
    title: Optional[str] = Field(None, alias="title")
    author: Optional[str] = Field(None, alias="author")
    date: Optional[str] = Field(None, alias="date")
    description: Optional[str] = Field(None, alias="description")
    keywords: Optional[str] = Field(None, alias="keywords")


# HTML PARSED -------------------------------------------------------------------------------------
# #################################################################################################
# TYPE DEF ----------------------------------------------------------------------------------------


ParsedContentUnion = Union[
    ParsedWebContent,
    ParsedWebContentSuccess,
    ParsedWebContentFailure,
    ParsedWebContentHtml,
    ParsedWebContentPdf,
    ParsedWebContentXmlSitemapResult
]

TextChunks = Dict[int, str]

# TYPE DEF ----------------------------------------------------------------------------------------
# #################################################################################################
