from datetime import datetime
from functools import reduce
from hashlib import md5
from typing import Dict, Optional, List, Set, Tuple, Any

from pydantic import Field, BaseModel, AnyUrl, field_validator, root_validator
from pydantic.main import IncEx
from typing_extensions import Union, Literal

from unibas.common.environment.variables import ModelDumpVariables
from unibas.common.model.model_mongo import MongoModel
from unibas.common.model.model_resource import WebContent, WebResource


# #################################################################################################
# GENERIC  ----------------------------------------------------------------------------------------

class ParsedWebContent(WebContent):
    """
    Model representing parsed web content.

    Attributes:
        resource_type (Literal['parsed_web_content']): The type of the resource.
        success (bool): Indicates if the parsing was successful.
    """
    resource_type: Literal['parsed_web_content'] = Field(default='parsed_web_content', frozen=True)
    success: bool


class ParsedWebContentSuccess(ParsedWebContent):
    """
    Model representing successfully parsed web content.

    Attributes:
        resource_type (Literal['parsed_web_content_success']): The type of the resource.
        success (bool): Indicates if the parsing was successful (always True).
    """
    resource_type: Literal['parsed_web_content_success'] = Field(default='parsed_web_content_success', frozen=True)
    success: bool = Field(True, frozen=True)


class ParsedWebContentTextChunks(ParsedWebContentSuccess):
    """
    Model representing parsed web content with text chunks.

    Attributes:
        resource_type (Literal['parsed_web_content_text_chunks']): The type of the resource.
        text_chunks (Dict[int, str]): Dictionary of text chunks indexed by their position.
    """
    resource_type: Literal['parsed_web_content_text_chunks'] = Field(default='parsed_web_content_text_chunks', frozen=True)
    text_chunks: Dict[int, str] = Field(default_factory=dict, alias="text_chunks")


class ParsedWebContentFailure(ParsedWebContent):
    """
    Model representing failed parsed web content.

    Attributes:
        resource_type (Literal['parsed_web_content_failure']): The type of the resource.
        success (bool): Indicates if the parsing was successful (always False).
        implemented (bool): Indicates if the failure was due to an unimplemented feature.
        reason (str): The reason for the failure.
    """
    resource_type: Literal['parsed_web_content_failure'] = Field(default='parsed_web_content_failure', frozen=True)
    success: bool = Field(False, frozen=True)
    implemented: bool = Field(...)
    reason: str = Field(...)

    @classmethod
    def create(cls, content: WebContent, reason: Union[RuntimeError, Exception, str, None]) -> 'ParsedWebContentFailure':
        """
        Create a ParsedWebContentFailure instance.

        Args:
            content (WebContent): The original web content.
            reason (Union[RuntimeError, Exception, str, None]): The reason for the failure.

        Returns:
            ParsedWebContentFailure: The created instance.
        """
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
    """
    Model representing parsed web content for an XML sitemap.

    Attributes:
        resource_type (Literal['parsed_web_content_xml_sitemap']): The type of the resource.
        content (List[WebResource]): List of web resources parsed from the XML sitemap.
    """
    resource_type: Literal['parsed_web_content_xml_sitemap'] = Field(default='parsed_web_content_xml_sitemap', frozen=True)
    content: List[WebResource] = Field(default_factory=list, alias="content")
    filter_paths: Optional[List[str]] = Field(None, alias="filter")
    modified_after: Optional[datetime] = Field(None, alias="filter")
    modified_before: Optional[datetime] = Field(None, alias="filter")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        print(f'Dumping XML sitemap {kwargs}')
        stringify_datetime: bool = kwargs.get('stringify_datetime', False)
        resources = [resource.model_dump(**kwargs.copy()) for resource in self.content]
        dump = {
            **super().model_dump(**kwargs),
            'content': resources
        }
        if stringify_datetime and self.modified_after is not None:
            dump['modified_after'] = self.modified_after.isoformat()
        if stringify_datetime and self.modified_before is not None:
            dump['modified_before'] = self.modified_before.isoformat()
        return dump

    def set_filter_paths(self, filter_paths: List[str]):
        """
        Set the filter paths for the XML sitemap.

        Args:
            filter_paths (List[str]): The filter paths.
        """
        self.filter_paths = filter_paths

    def set_modified_after(self, modified_after: datetime):
        """
        Set the modified after date for the XML sitemap.

        Args:
            modified_after (datetime): The modified after date.
        """
        self.modified_after = modified_after

    def set_modified_before(self, modified_before: datetime):
        """
        Set the modified before date for the XML sitemap.

        Args:
            modified_before (datetime): The modified before date.
        """
        self.modified_before = modified_before


# XML PARSED --------------------------------------------------------------------------------------
# #################################################################################################
# HTML PARSED -------------------------------------------------------------------------------------


class ParsedWebContentHtml(ParsedWebContentTextChunks):
    """
    Model representing parsed web content in HTML format.

    Attributes:
        resource_type (Literal['parsed_web_content_success']): The type of the resource.
        attributes (HtmlAttributes): The HTML attributes of the parsed content.
        content (TextChunks): The text chunks of the parsed content.
    """
    resource_type: Literal['parsed_web_content_success'] = Field(default='parsed_web_content_html', frozen=True)
    attributes: 'HtmlAttributes' = Field(..., alias="attributes")
    content: 'TextChunks' = Field(default_factory=list, alias="content")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        return {
            **super().model_dump(**kwargs),
            'attributes': self.attributes.model_dump(**kwargs),
            'content': self.content
        }


class HtmlAttributes(BaseModel):
    """
    Model representing HTML attributes.

    Attributes:
        title (Optional[str]): The title of the HTML content.
        author (Optional[str]): The author of the HTML content.
        date (Optional[str]): The date of the HTML content.
        description (Optional[str]): The description of the HTML content.
        keywords (Optional[str]): The keywords of the HTML content.
        links (UrlParseResult): The parsed URLs from the HTML content.
    """
    title: Optional[str] = Field(..., alias="title")
    author: Optional[str] = Field(..., alias="author")
    date: Optional[str] = Field(..., alias="date")
    description: Optional[str] = Field(..., alias="description")
    keywords: Optional[str] = Field(..., alias="keywords")
    links: 'UrlParseResult' = Field(..., alias="links")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        return {
            **super().model_dump(**kwargs),
            'links': self.links.model_dump()
        }


def _url_arche_key(origin: AnyUrl, target: AnyUrl) -> str:
    return md5(string=bytes(f'{origin}:{target}', 'utf-8'), usedforsecurity=False).hexdigest()


class UrlArche(BaseModel):
    """
    Model representing a URL arche.

    Attributes:
        origin (AnyUrl): The origin URL.
        target (AnyUrl): The target URL.
        weight (Optional[float]): The weight of the URL arche.
    """
    origin: AnyUrl = Field(..., alias="origin")
    target: AnyUrl = Field(..., alias="target")
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
        """
        Generate a unique key for the URL arche.

        Returns:
            str: The unique key.
        """
        return self.key

    def merge(self, arche: 'UrlArche'):
        """
        Merge another URL arche into this one by adding their weights.

        Args:
            arche (UrlArche): The URL arche to merge.
        """
        self.weight += arche.weight


class UrlGraph(MongoModel):
    """
    Model representing a graph of URLs.

    Attributes:
        nodes (Set[AnyUrl]): The set of nodes (URLs) in the graph.
        arches (Dict[str, UrlArche]): The dictionary of URL arches in the graph.
    """
    nodes: Set[AnyUrl] = Field(default_factory=set)
    arches: Dict[str, UrlArche] = Field(default_factory=dict)

    def add_arche(self, arche: UrlArche):
        """
        Add a URL arche to the graph.

        Args:
            arche (UrlArche): The URL arche to add.
        """
        self.nodes.add(arche.origin)
        self.nodes.add(arche.target)
        if arche.key in self.arches:
            self.arches[arche.key].merge(arche)
        else:
            self.arches[arche.key] = arche

    def merge(self, graph: 'UrlGraph'):
        """
        Merge another URL graph into this one.

        Args:
            graph (UrlGraph): The URL graph to merge.
        """
        for arche in graph.arches.values():
            self.add_arche(arche)

    @staticmethod
    def merge_all(graphs: List['UrlGraph']) -> 'UrlGraph':
        """
        Merge a list of URL graphs into a single graph.

        Args:
            graphs (List[UrlGraph]): The list of URL graphs to merge.

        Returns:
            UrlGraph: The merged URL graph.
        """
        return reduce(lambda g1, g2: (g1.merge(g2), g1)[1], graphs, UrlGraph())

    def get_outgoing_arches(self, origin: AnyUrl) -> List[UrlArche]:
        """
        Get the list of outgoing URL arches from a given origin URL.

        Args:
            origin (AnyUrl): The origin URL.

        Returns:
            List[UrlArche]: The list of outgoing URL arches.
        """
        if origin not in self.nodes:
            return []
        keys = [_url_arche_key(origin, target) for target in self.nodes if target != origin]
        return [self.arches[key] for key in keys if key in self.arches]

    def get_incoming_arches(self, target: AnyUrl) -> List[UrlArche]:
        """
        Get the list of incoming URL arches to a given target URL.

        Args:
            target (AnyUrl): The target URL.

        Returns:
            List[UrlArche]: The list of incoming URL arches.
        """
        if target not in self.nodes:
            return []
        keys = [_url_arche_key(origin, target) for origin in self.nodes if origin != target]
        return [self.arches[key] for key in keys if key in self.arches]

    def get_all_arches_for(self, url: AnyUrl) -> List[UrlArche]:
        """
        Get all URL arches for a given URL.

        Args:
            url (AnyUrl): The URL.

        Returns:
            List[UrlArche]: The list of URL arches.
        """
        return self.get_outgoing_arches(url) + self.get_incoming_arches(url)

    def model_dump(self, **kwargs) -> dict[str, Any]:
        return {
            **super().model_dump(**kwargs),
            'arches': {key: arche.model_dump(**kwargs) for key, arche in self.arches.items()}
        }


class UrlParseResult(MongoModel):
    """
    Model representing the result of parsing URLs.

    Attributes:
        origin (AnyUrl): The origin URL.
        urls (List[Tuple[AnyUrl, int]]): The list of parsed URLs with their frequencies.
    """
    origin: AnyUrl = Field()
    urls: List[Tuple[AnyUrl, int]] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """
        Check if the URL parse result is empty.

        Returns:
            bool: True if empty, False otherwise.
        """
        return len(self.urls) == 0

    def get_urls(self) -> List[AnyUrl]:
        """
        Get the list of parsed URLs.

        Returns:
            List[AnyUrl]: The list of parsed URLs.
        """
        return [url for url, _ in self.urls]

    def get_urls_with_freq(self) -> List[Tuple[AnyUrl, int]]:
        """
        Get the list of parsed URLs with their frequencies.

        Returns:
            List[Tuple[AnyUrl, int]]: The list of parsed URLs with their frequencies.
        """
        return self.urls

    def get_origin(self) -> AnyUrl:
        """
        Get the origin URL.

        Returns:
            AnyUrl: The origin URL.
        """
        return self.origin

    def get_urls_from_same_host_from_origin(self) -> List[AnyUrl]:
        """
        Get the list of URLs from the same host as the origin.

        Returns:
            List[AnyUrl]: The list of URLs from the same host.
        """
        return list(filter(lambda url: self.origin.host == url.host, self.get_urls()))

    def get_urls_from_different_host_from_origin(self) -> List[AnyUrl]:
        """
        Get the list of URLs from a different host than the origin.

        Returns:
            List[AnyUrl]: The list of URLs from a different host.
        """
        return list(filter(lambda url: self.origin.host != url.host, self.get_urls()))

    def get_graph_data(self) -> UrlGraph:
        """
        Get the URL graph data.

        Returns:
            UrlGraph: The URL graph data.
        """
        graph = UrlGraph()
        for url, freq in self.urls:
            graph.add_arche(UrlArche(origin=self.origin, target=url, weight=freq))
        return graph


# HTML PARSED -------------------------------------------------------------------------------------
# #################################################################################################
# PDF PARSED --------------------------------------------------------------------------------------

class ParsedWebContentPdf(ParsedWebContentTextChunks):
    """
    Model representing parsed web content in PDF format.

    Attributes:
        resource_type (Literal['parsed_web_content_pdf']): The type of the resource.
        attributes (PdfAttributes): The PDF attributes of the parsed content.
        content (TextChunks): The text chunks of the parsed content.
    """
    resource_type: Literal['parsed_web_content_pdf'] = Field(default='parsed_web_content_pdf', frozen=True)
    attributes: 'PdfAttributes' = Field(..., alias="attributes")
    content: 'TextChunks' = Field(default_factory=list, alias="content")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        return {
            **super().model_dump(**kwargs),
            'attributes': self.attributes.model_dump(**kwargs),
            'content': self.content
        }


class PdfAttributes(BaseModel):
    """
    Model representing PDF attributes.

    Attributes:
        title (Optional[str]): The title of the PDF content.
        author (Optional[str]): The author of the PDF content.
        date (Optional[str]): The date of the PDF content.
        description (Optional[str]): The description of the PDF content.
        keywords (Optional[str]): The keywords of the PDF content.
    """
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
"""
Union type representing various parsed web content models.
"""

TextChunks = Dict[int, str]
"""
Type alias for a dictionary of text chunks indexed by their position.
"""

# TYPE DEF ----------------------------------------------------------------------------------------
# #################################################################################################
