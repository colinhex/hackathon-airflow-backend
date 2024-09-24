from enum import Enum


class Charset(str, Enum):
    UNKNOWN = 'unknown'
    UTF_8 = 'utf-8'
    UTF_16 = 'utf-16'
    UTF_32 = 'utf-32'
    ISO_8859_1 = 'iso-8859-1'
    ISO_8859_2 = 'iso-8859-2'
    ISO_8859_3 = 'iso-8859-3'
    ISO_8859_4 = 'iso-8859-4'
    ISO_8859_5 = 'iso-8859-5'
    ISO_8859_6 = 'iso-8859-6'
    ISO_8859_7 = 'iso-8859-7'
    ISO_8859_8 = 'iso-8859-8'
    ISO_8859_9 = 'iso-8859-9'
    WINDOWS_1250 = 'windows-1250'
    WINDOWS_1251 = 'windows-1251'
    WINDOWS_1252 = 'windows-1252'
    WINDOWS_1253 = 'windows-1253'
    WINDOWS_1254 = 'windows-1254'
    WINDOWS_1255 = 'windows-1255'
    WINDOWS_1256 = 'windows-1256'
    WINDOWS_1257 = 'windows-1257'
    WINDOWS_1258 = 'windows-1258'

    @staticmethod
    def from_name(name: str):
        return Charset[name.replace('-', '_').upper()]

    @staticmethod
    def default_to_charset(default_to_utf8: bool = False) -> 'Charset':
        if default_to_utf8:
            return Charset.UTF_8
        return Charset.UNKNOWN

    @staticmethod
    def from_content_type(content_type: str, default_to_utf8: bool = False) -> 'Charset':
        if content_type is None:
            return Charset.default_to_charset(default_to_utf8=default_to_utf8)
        charset: str | None = content_type.split(';')[1].strip() if ';' in content_type else None
        if charset is not None and '=' in charset:
            charset = charset.split('=')[1].strip()
        return Charset[charset.replace('-', '_').upper()] if charset else Charset.default_to_charset(default_to_utf8=default_to_utf8)

    @staticmethod
    def get_all():
        return list(map(lambda x: x.value, Charset))


