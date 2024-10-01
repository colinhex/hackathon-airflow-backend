import re
from datetime import datetime, timezone
from typing import Literal, Union, Optional, List
from urllib.parse import urlparse

from aiohttp import ClientResponse
from pydantic import BaseModel, AnyHttpUrl, Field, ConfigDict, AnyUrl

from unibas.common.model.model_annotations import MongoAnyHttpUrl, MongoDatetime
from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_mime_type import MimeType, is_in_mime_type_group, JSON_MIME_TYPE, TEXT_MIME_TYPE, \
    BINARY_MIME_TYPE
from unibas.common.model.model_mongo import MongoModel


class WebResource(MongoModel):
    model_config = ConfigDict(**MongoModel.model_config)
    resource_type: Literal['web_resource'] = Field(default='web_resource', frozen=True)
    loc: MongoAnyHttpUrl
    lastmod: Optional[MongoDatetime] = Field(default=None)

    def was_modified_after(self, date: datetime | str, accept_none=False) -> bool:
        if accept_none and date is None:
            return True
        compare: datetime = datetime.fromisoformat(date) if isinstance(date, str) else date
        return compare.astimezone(tz=timezone.utc) < self.lastmod.astimezone(tz=timezone.utc)

    def was_modified_before(self, date: datetime | str | None, accept_none=False) -> bool:
        if accept_none and date is None:
            return True
        compare: datetime = datetime.fromisoformat(date) if isinstance(date, str) else date
        return compare.astimezone(tz=timezone.utc) > self.lastmod.astimezone(tz=timezone.utc)

    def is_same_host(self, domain: str | AnyHttpUrl | 'WebResource') -> bool:
        if isinstance(domain, str):
            return urlparse(domain).netloc == self.loc.host
        elif isinstance(domain, AnyHttpUrl):
            return domain.host == self.loc.host
        elif isinstance(domain, WebResource):
            return self.is_same_host(domain.loc)

    def matches(self, path: re.Pattern) -> bool:
        if str(path).startswith('/') or str(path).startswith('^/'):
            if self.loc.path is None and not (str(path) == '/' or str(path) == ''):
                return False
            return path.match(str(self.loc.path)) is not None
        return path.match(str(self.loc)) is not None

    def matches_any(self, paths: List[re.Pattern], accept_none=True, accept_empty=True) -> bool:
        if (paths is None and accept_none) or (len(paths) == 0 and accept_empty):
            return True
        return any([self.matches(p) for p in paths])

    def is_sub_path_from(self, path: Union[str, AnyUrl]) -> bool:
        if isinstance(path, AnyUrl):
            path = str(path)
            return str(self.loc).startswith(path)
        elif isinstance(path, str):
            if path.startswith('/'):
                if self.loc.path is None and not (path == '/' or path == ''):
                    return False
                return str(self.loc.path).startswith(path)
            return str(self.loc).startswith(path)
        raise ValueError(f'Invalid path type: {type(path)}')

    def is_sub_path_from_any(self, path: List[Union[str, AnyUrl]] | None, accept_none=True, accept_empty=True) -> bool:
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
        filtered = []
        for resource in resources:
            if resource.is_sub_path_from_any(filter_paths, accept_none=True, accept_empty=True) \
                    and resource.was_modified_after(modified_after, accept_none=True)\
                    and resource.was_modified_before(modified_before, accept_none=True):
                filtered.append(resource)
        return filtered


class WebContentHeader(WebResource):
    model_config = ConfigDict(**WebResource.model_config)
    model_config.update(
        use_enum_values=True,
    )
    resource_type: Literal['web_content_header'] = Field(default='web_content_header', frozen=True)
    code: HttpCode = Field(default=HttpCode.UNKNOWN)
    mime_type: MimeType = Field(default=MimeType.UNKNOWN)
    charset: Charset = Field(default=Charset.UNKNOWN)
    extracted_at: MongoDatetime = Field(default_factory=datetime.now)

    @classmethod
    async def result(cls, web_resource: WebResource, client_response: ClientResponse) -> 'WebContentHeader':
        code: HttpCode = HttpCode.from_status_code(client_response.status)
        mime_type = MimeType.from_content_type(client_response.headers.get('Content-Type'))
        charset = Charset.from_content_type(client_response.headers.get('Content-Type'), default_to_utf8=True)

        lastmod = client_response.headers.get('Last-Modified')
        if lastmod is not None:
            lastmod = datetime.strptime(lastmod, "%a, %d %b %Y %H:%M:%S %Z")
        else:
            lastmod = None

        return cls(
            loc=web_resource.loc,
            lastmod=lastmod,
            code=code,
            mime_type=mime_type,
            charset=charset
        )


class WebContent(WebContentHeader):
    model_config = ConfigDict(**WebContentHeader.model_config)
    model_config.update(
        use_enum_values=True,
    )

    resource_type: Literal['web_content'] = Field(default='web_content', frozen=True)
    content: Union[bytes, str]

    @classmethod
    async def result(cls, web_resource: WebResource, client_response: ClientResponse) -> 'WebContent':
        code: HttpCode = HttpCode.from_status_code(client_response.status)
        mime_type = MimeType.from_content_type(client_response.headers.get('Content-Type'))
        charset = Charset.from_content_type(client_response.headers.get('Content-Type'), default_to_utf8=True)

        lastmod = client_response.headers.get('Last-Modified')
        if lastmod is not None:
            lastmod = datetime.strptime(lastmod, "%a, %d %b %Y %H:%M:%S %Z")
        else:
            lastmod = None

        update_last_mod = False
        if lastmod is not None and web_resource.lastmod is None:
            # If the lastmod is not set in the web resource, update it.
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


class ApiResource(BaseModel):
    resource_type: Literal['api_resource'] = Field(default='api_resource', frozen=True)


WebResourceUnion = Union[
    WebResource,
    WebContentHeader,
    WebContent
]
