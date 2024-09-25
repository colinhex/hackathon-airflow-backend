from datetime import datetime, timezone
from typing import Any, Literal, Union, Optional, List
from urllib.parse import urlparse

from aiohttp import ClientResponse
from pydantic import BaseModel, AnyHttpUrl, Field, ConfigDict, AnyUrl

from unibas.common.model.charset_model import Charset
from unibas.common.model.http_model import HttpCode
from unibas.common.model.mime_model import MimeType, is_in_mime_type_group, JSON_MIME_TYPE, TEXT_MIME_TYPE, \
    BINARY_MIME_TYPE
from unibas.common.model.mongo_model import MongoModel
from unibas.common.environment import ModelDumpVariables, ResourceVariables


class WebResource(MongoModel):
    resource_type: Literal['web_resource'] = Field(default='web_resource', frozen=True)
    loc: AnyHttpUrl
    lastmod: Optional[datetime] = Field(default=None)

    @classmethod
    def from_iso_string(cls, loc: str, lastmod: str):
        return WebResource(loc=loc, lastmod=datetime.fromisoformat(lastmod))

    def was_modified_after(self, date: datetime | str, accept_none=False) -> bool:
        if accept_none and date is None:
            return True
        compare: datetime = datetime.fromisoformat(date) if isinstance(date, str) else date
        return compare < self.lastmod

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

    def is_sub_path_from(self, path: str) -> bool:
        return str(self.loc.path).startswith(path)

    def is_sub_path_from_any(self, path: List[str] | None, accept_none=True, accept_empty=True) -> bool:
        if (path is None and accept_none) or (len(path) == 0 and accept_empty):
            return True
        return any([self.is_sub_path_from(p) for p in path])

    @staticmethod
    def filter(resources: List['WebResource'], filter_paths: List[AnyUrl] | None = None, modified_after: datetime | None = None):
        filtered = []
        for resource in resources:
            if resource.is_sub_path_from_any(filter_paths, accept_none=True, accept_empty=True) \
                    and resource.was_modified_before(modified_after, accept_none=True):
                filtered.append(resource)
        return filtered

    def model_dump(self, **kwargs) -> dict[str, Any]:
        stringify_url = kwargs.pop(ModelDumpVariables.STRINGIFY_URL, True)
        stringify_datetime = kwargs.pop(ModelDumpVariables.STRINGIFY_DATETIME, False)

        dump = super().model_dump(**kwargs)

        if stringify_url:
            dump['loc'] = str(dump['loc'])
        if stringify_datetime:
            dump['lastmod'] = dump['lastmod'].isoformat()

        return dump


class WebContent(WebResource):
    model_config = ConfigDict(use_enum_values=True)
    resource_type: Literal['web_response'] = Field(default='web_response', frozen=True)
    code: HttpCode = Field(default=HttpCode.UNKNOWN)
    mime_type: MimeType = Field(default=MimeType.UNKNOWN)
    charset: Charset = Field(default=Charset.UNKNOWN)
    extracted_at: datetime = Field(default_factory=datetime.now)
    content: Union[bytes, str]

    @classmethod
    async def result(cls, web_resource: WebResource, client_response: ClientResponse) -> 'WebContent':
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
            loc=str(web_resource.loc),
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
