from enum import Enum
from typing import Literal


class HttpCode(int, Enum):
    """
    Enum representing various HTTP status codes.
    """

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
        """
        Get an HttpCode enum member from a status code.

        Args:
            code (int): The HTTP status code.

        Returns:
            HttpCode: The corresponding HttpCode enum member.
        """
        return cls(code)

    @classmethod
    def from_name(cls, name: str) -> 'HttpCode':
        """
        Get an HttpCode enum member from a string name.

        Args:
            name (str): The name of the HTTP status code.

        Returns:
            HttpCode: The corresponding HttpCode enum member.
        """
        return HttpCode[name.upper()]

    def get_name(self) -> str:
        """
        Get the name of the HTTP status code in lowercase.

        Returns:
            str: The name of the HTTP status code in lowercase.
        """
        return self.name.lower()

    @staticmethod
    def _is_code_group(code: int, group: Literal[1, 2, 3, 4, 5]) -> bool:
        """
        Check if the HTTP status code belongs to a specific group.

        Args:
            group (Literal[1, 2, 3, 4, 5]): The group number (1-5).

        Returns:
            bool: True if the status code belongs to the specified group, False otherwise.
        """
        return str(code).startswith(str(group))

    @staticmethod
    def protocol(code: int) -> bool:
        """
        Check if the HTTP status code is in the 1xx group.

        Returns:
            bool: True if the status code is in the 1xx group, False otherwise.
        """
        return HttpCode._is_code_group(code, 1)

    @staticmethod
    def success(code: int) -> bool:
        """
        Check if the HTTP status code is in the 2xx group.

        Returns:
            bool: True if the status code is in the 2xx group, False otherwise.
        """
        return HttpCode._is_code_group(code, 2)

    @staticmethod
    def redirect(code: int) -> bool:
        """
        Check if the HTTP status code is in the 3xx group.

        Returns:
            bool: True if the status code is in the 3xx group, False otherwise.
        """
        return HttpCode._is_code_group(code, 3)

    @staticmethod
    def client_error(code: int) -> bool:
        """
        Check if the HTTP status code is in the 4xx group.

        Returns:
            bool: True if the status code is in the 4xx group, False otherwise.
        """
        return HttpCode._is_code_group(code, 4)

    @staticmethod
    def server_error(code: int) -> bool:
        """
        Check if the HTTP status code is in the 5xx group.

        Returns:
            bool: True if the status code is in the 5xx group, False otherwise.
        """
        return HttpCode._is_code_group(code, 5)