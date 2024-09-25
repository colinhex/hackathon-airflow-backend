from datetime import datetime, timezone
from typing import Any, Literal, Union, Optional, List
from urllib.parse import urlparse

from aiohttp import ClientResponse
from pydantic import BaseModel, AnyHttpUrl, Field, ConfigDict, AnyUrl, ValidationError, field_validator

from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_mime_type import MimeType, is_in_mime_type_group, JSON_MIME_TYPE, TEXT_MIME_TYPE, \
    BINARY_MIME_TYPE
from unibas.common.model.model_mongo import MongoModel
from unibas.common.environment.variables import ModelDumpVariables, ResourceVariables


class WebResource(MongoModel):
    """
    Model representing a web resource.

    Attributes:
        model_config (ConfigDict): Configuration for the model.
        resource_type (Literal['web_resource']): The type of the resource, fixed to 'web_resource'.
        loc (AnyHttpUrl): The URL of the web resource.
        lastmod (Optional[datetime]): The last modification date of the web resource.
    """
    model_config = ConfigDict(**MongoModel.model_config)
    resource_type: Literal['web_resource'] = Field(default='web_resource', frozen=True)
    loc: AnyHttpUrl
    lastmod: Optional[datetime] = Field(default=None)

    @classmethod
    def from_iso_string(cls, loc: str, lastmod: str):
        """
        Create a WebResource instance from ISO formatted strings.

        Args:
            loc (str): The URL of the web resource.
            lastmod (str): The last modification date in ISO format.

        Returns:
            WebResource: The created WebResource instance.
        """
        return WebResource(loc=loc, lastmod=datetime.fromisoformat(lastmod))

    def was_modified_after(self, date: datetime | str, accept_none=False) -> bool:
        """
        Check if the resource was modified after a given date.

        Args:
            date (datetime | str): The date to compare with.
            accept_none (bool, optional): Whether to accept None as a valid date. Defaults to False.

        Returns:
            bool: True if the resource was modified after the given date, False otherwise.
        """
        if accept_none and date is None:
            return True
        compare: datetime = datetime.fromisoformat(date) if isinstance(date, str) else date
        return compare < self.lastmod

    def was_modified_before(self, date: datetime | str | None, accept_none=False) -> bool:
        """
        Check if the resource was modified before a given date.

        Args:
            date (datetime | str | None): The date to compare with.
            accept_none (bool, optional): Whether to accept None as a valid date. Defaults to False.

        Returns:
            bool: True if the resource was modified before the given date, False otherwise.
        """
        if accept_none and date is None:
            return True
        compare: datetime = datetime.fromisoformat(date) if isinstance(date, str) else date
        return compare.astimezone(tz=timezone.utc) > self.lastmod.astimezone(tz=timezone.utc)

    def is_same_host(self, domain: str | AnyHttpUrl | 'WebResource') -> bool:
        """
        Check if the resource is from the same host as the given domain.

        Args:
            domain (str | AnyHttpUrl | WebResource): The domain to compare with.

        Returns:
            bool: True if the resource is from the same host, False otherwise.
        """
        if isinstance(domain, str):
            return urlparse(domain).netloc == self.loc.host
        elif isinstance(domain, AnyHttpUrl):
            return domain.host == self.loc.host
        elif isinstance(domain, WebResource):
            return self.is_same_host(domain.loc)

    def is_sub_path_from(self, path: Union[str, AnyUrl]) -> bool:
        """
        Check if the resource's path is a sub-path of the given path.

        Args:
            path (Union[str, AnyUrl]): The path to compare with.

        Returns:
            bool: True if the resource's path is a sub-path, False otherwise.
        """
        path_string = str(path)
        if path_string.startswith('/'):
            return str(self.loc.path).startswith(path)
        return str(self.loc).startswith(path_string)

    def is_sub_path_from_any(self, path: List[Union[str, AnyUrl]] | None, accept_none=True, accept_empty=True) -> bool:
        """
        Check if the resource's path is a sub-path of any given paths.

        Args:
            path (List[Union[str, AnyUrl]] | None): The list of paths to compare with.
            accept_none (bool, optional): Whether to accept None as a valid path. Defaults to True.
            accept_empty (bool, optional): Whether to accept an empty list as valid. Defaults to True.

        Returns:
            bool: True if the resource's path is a sub-path of any given paths, False otherwise.
        """
        if (path is None and accept_none) or (len(path) == 0 and accept_empty):
            return True
        return any([self.is_sub_path_from(p) for p in path])

    @staticmethod
    def filter(
            resources: List['WebResourceUnion'],
            filter_paths: List[Union[str, AnyUrl]] | None = None,
            modified_after: datetime | None = None,
            modified_before: datetime | None = None
    ) -> List['WebResourceUnion']:
        """
        Filter a list of web resources based on paths and modification dates.

        Args:
            resources (List[WebResource]): The list of web resources to filter.
            filter_paths (List[Union[str, AnyUrl]] | None, optional): The paths to filter by. Defaults to None.
            modified_after (datetime | None, optional): The date to filter resources modified after. Defaults to None.
            modified_before (datetime | None, optional): The date to filter resources modified before. Defaults to None.

        Returns:
            List[WebResource]: The filtered list of web resources.
        """
        filtered = []
        for resource in resources:
            if resource.is_sub_path_from_any(filter_paths, accept_none=True, accept_empty=True) \
                    and resource.was_modified_after(modified_after, accept_none=True)\
                    and resource.was_modified_before(modified_before, accept_none=True):
                filtered.append(resource)
        return filtered

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Dump the model data to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for dumping the model.

        Returns:
            dict[str, Any]: The dumped model data.
        """
        stringify_url = kwargs.pop(ModelDumpVariables.STRINGIFY_URL, True)
        stringify_datetime = kwargs.pop(ModelDumpVariables.STRINGIFY_DATETIME, False)
        print('Dumping web resource: stringify_url', stringify_url, 'stringify_datetime', stringify_datetime)

        dump = super().model_dump(**kwargs)

        if stringify_url:
            dump['loc'] = str(dump['loc'])
        if stringify_datetime and 'lastmod' in dump and dump['lastmod'] is not None:
            dump['lastmod'] = dump['lastmod'].isoformat()

        return dump


class WebContentHeader(WebResource):
    """
    Model representing web content headers, inheriting from WebResource.

    Attributes:
        model_config (ConfigDict): Configuration for the model.
        resource_type (Literal['web_response']): The type of the resource, fixed to 'web_response'.
        code (HttpCode): The HTTP status code of the response.
        mime_type (MimeType): The MIME type of the content.
        charset (Charset): The character set of the content.
        extracted_at (datetime): The datetime when the content was extracted.
    """
    model_config = ConfigDict(**WebResource.model_config)
    model_config.update(
        use_enum_values=True,
    )
    resource_type: Literal['web_content_header'] = Field(default='web_content_header', frozen=True)
    code: HttpCode = Field(default=HttpCode.UNKNOWN)
    mime_type: MimeType = Field(default=MimeType.UNKNOWN)
    charset: Charset = Field(default=Charset.UNKNOWN)
    extracted_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    async def result(cls, web_resource: WebResource, client_response: ClientResponse) -> 'WebContentHeader':
        """
        Create a WebContentHeader instance from a web resource and client response.

        Args:
            web_resource (WebResource): The web resource.
            client_response (ClientResponse): The client response.

        Returns:
            WebContentHeader: The created WebContentHeader instance.
        """
        code: HttpCode = HttpCode.from_status_code(client_response.status)
        mime_type = MimeType.from_content_type(client_response.headers.get('Content-Type'))
        charset = Charset.from_content_type(client_response.headers.get('Content-Type'), default_to_utf8=True)

        lastmod = client_response.headers.get('Last-Modified')
        if lastmod is not None:
            lastmod = datetime.strptime(lastmod, ResourceVariables.HEADER_DATE_FORMAT)
        else:
            lastmod = None

        return cls(
            loc=web_resource.loc,
            lastmod=lastmod,
            code=code,
            mime_type=mime_type,
            charset=charset
        )

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Dump the model data to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for dumping the model.

        Returns:
            dict[str, Any]: The dumped model data.
        """
        return super().model_dump(**kwargs)


class WebContent(WebContentHeader):
    """
    Model representing web content, inheriting from WebContentHeader.

    Attributes:
        model_config (ConfigDict): Configuration for the model.
        resource_type (Literal['web_response']): The type of the resource, fixed to 'web_response'.
        content (Union[bytes, str]): The content of the web resource.
    """
    model_config = ConfigDict(**WebContentHeader.model_config)
    model_config.update(
        use_enum_values=True,
    )

    resource_type: Literal['web_response'] = Field(default='web_content', frozen=True)
    content: Union[bytes, str]

    @classmethod
    async def result(cls, web_resource: WebResource, client_response: ClientResponse) -> 'WebContent':
        """
        Create a WebContent instance from a web resource and client response.

        Args:
            web_resource (WebResource): The web resource.
            client_response (ClientResponse): The client response.

        Returns:
            WebContent: The created WebContent instance.

        Raises:
            ValueError: If the MIME type is unexpected.
        """
        code: HttpCode = HttpCode.from_status_code(client_response.status)
        mime_type = MimeType.from_content_type(client_response.headers.get('Content-Type'))
        charset = Charset.from_content_type(client_response.headers.get('Content-Type'), default_to_utf8=True)

        lastmod = client_response.headers.get('Last-Modified')
        if lastmod is not None:
            lastmod = datetime.strptime(lastmod, ResourceVariables.HEADER_DATE_FORMAT)
        else:
            lastmod = None

        update_last_mod = False
        if lastmod is not None and web_resource.lastmod is not None:
            if web_resource.was_modified_before(lastmod):
                update_last_mod = True

        content: Union[bytes, str]
        if is_in_mime_type_group(mime_type, JSON_MIME_TYPE):
            content = await client_response.json()
        elif is_in_mime_type_group(mime_type, TEXT_MIME_TYPE):
            content = await client_response.text()
        elif is_in_mime_type_group(mime_type, BINARY_MIME_TYPE):
            content = await client_response.read()
        else:
            raise ValueError(f'Unexpected mime type: {client_response.headers.get("Content-Type")}')

        return cls(
            loc=web_resource.loc,
            lastmod=web_resource.lastmod if (
                    not update_last_mod and web_resource.lastmod is not None
            ) else lastmod,
            code=code,
            mime_type=mime_type,
            charset=charset,
            content=content
        )

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Dump the model data to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for dumping the model.

        Returns:
            dict[str, Any]: The dumped model data.
        """
        return super().model_dump(**kwargs)


class ApiContent(BaseModel):
    resource_type: Literal['api_resource'] = Field(default='api_content', frozen=True)


WebResourceUnion = Union[WebResource, WebContentHeader, WebContent]
