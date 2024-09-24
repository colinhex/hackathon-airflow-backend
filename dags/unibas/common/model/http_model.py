
from enum import Enum
from typing import Literal


class HttpCode(int, Enum):
    UNKNOWN = 0

    # 1xx: Informational Responses
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    PROCESSING = 102

    # 2xx: Success Responses
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206

    # 3xx: Redirection Responses
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    # 4xx: Client Error Responses
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PAYLOAD_TOO_LARGE = 413
    UNSUPPORTED_MEDIA_TYPE = 415
    TOO_MANY_REQUESTS = 429

    # 5xx: Server Error Responses
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505

    @classmethod
    def from_status_code(cls, code: int) -> 'HttpCode':
        return cls(code)

    @classmethod
    def from_name(cls, name: str) -> 'HttpCode':
        return HttpCode[name.upper()]

    def get_name(self) -> str:
        return self.name.lower()

    def _is_code_group(self, group: Literal[1, 2, 3, 4, 5]):
        return str(self.value).startswith(str(group))

    def protocol(self) -> bool:
        return self._is_code_group(1)

    def success(self):
        return self._is_code_group(2)

    def redirect(self):
        return self._is_code_group(3)

    def client_error(self):
        return self._is_code_group(4)

    def server_error(self):
        return self._is_code_group(5)


