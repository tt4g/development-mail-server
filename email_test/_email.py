from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from email.header import Header
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Generic, Iterable, Optional, TypeVar, Union


@dataclass(frozen=True)
class EmailAddress:
    """電子メールアドレス。"""

    address: str
    """メールアドレス。
    """
    name: Optional[str]
    """表示名。"""


@dataclass(frozen=True)
class FormattedEmailAddress:
    """フォーマットされた電子メールアドレス。

    address only Example: ``example@example.com``

    address with display name Example: ``John Smith <example@example.com>``
    """

    value: str


class EmailAddressConvertProtocol(metaclass=ABCMeta):
    """`EmailAddress` を `FormattedEmailAddress` に変換する。"""

    @abstractmethod
    def to_formatted(self) -> FormattedEmailAddress:
        """`FormattedEmailAddress` を生成する。

        :return: `FormattedEmailAddress`
        :rtype: FormattedEmailAddress
        """
        ...


class AsciiEmailAddress(EmailAddressConvertProtocol):
    __email_address: EmailAddress

    def __init__(self, email_address: EmailAddress) -> None:
        """Initialize.

        :param email_address: `EmailAddress`
        :type email_address: EmailAddress
        """
        self.__email_address = email_address

    def to_formatted(self) -> FormattedEmailAddress:
        return format_email_address(
            email_address=self.__email_address, charset=r"ascii"
        )


class NonAsciiEmailAddress(EmailAddressConvertProtocol):
    __email_address: EmailAddress
    __charset: str

    def __init__(self, email_address: EmailAddress, charset: str) -> None:
        """Initialize.

        :param email_address: `EmailHeader`
        :type email_address: EmailHeader
        :param charset: メールアドレス表示名の文字エンコーディング。
        :type charset: str
        """
        self.__email_address = email_address
        self.__charset = charset

    def to_formatted(self) -> FormattedEmailAddress:
        return format_email_address(
            email_address=self.__email_address, charset=self.__charset
        )


MimeEmailAddress = Union[AsciiEmailAddress, NonAsciiEmailAddress]


def format_email_address(
    email_address: EmailAddress, charset: str
) -> FormattedEmailAddress:
    """Convert `EmailAddress` to `FormattedEmailAddress`.

    :param email_address: `EmailAddress`
    :type email_address: EmailAddress
    :param charset: メールアドレス表示名の文字エンコーディング。
    :type charset: str
    :return: `FormattedEmailAddress`
    :rtype: FormattedEmailAddress
    """
    name_and_address = (email_address.name, email_address.address)
    formatted = formataddr(name_and_address, charset=charset)

    return FormattedEmailAddress(value=formatted)


def format_recipient_header(mime_email_addresses: Iterable[MimeEmailAddress]) -> str:
    def _to_formatted(mime_email_address: MimeEmailAddress) -> str:
        return mime_email_address.to_formatted().value

    return r",".join(map(_to_formatted, mime_email_addresses))


@dataclass(frozen=True)
class Subject:
    """`Subject` header."""

    value: str


@dataclass(frozen=True)
class EmailHeader:
    """Email header."""

    name: str
    """Header name."""
    value: str
    """Header value."""


class HeaderConvertProtocol(metaclass=ABCMeta):
    """`EmailHeader` を `Header` に変換する。"""

    @abstractmethod
    def get_name(self) -> str:
        """ヘッダー名を返す。

        :return: ヘッダー名。
        :rtype: str
        """
        ...

    @abstractmethod
    def to_header(self) -> Header:
        """`Header` を生成する。

        :return: `Header`
        :rtype: Header
        """
        ...


class AsciiEmailHeader(HeaderConvertProtocol):
    __email_header: EmailHeader

    def __init__(self, email_header: EmailHeader) -> None:
        """Initialize.

        :param email_header: `EmailHeader`
        :type email_header: EmailHeader
        """
        self.__email_header = email_header

    def get_name(self) -> str:
        return self.__email_header.name

    def to_header(self) -> Header:
        return Header(self.__email_header.value)


class NonAsciiEmailHeader(HeaderConvertProtocol):
    __email_header: EmailHeader
    __charset: str

    def __init__(self, email_header: EmailHeader, charset: str) -> None:
        """Initialize.

        :param email_header: `EmailHeader`
        :type email_header: EmailHeader
        :param charset: ヘッダーの文字エンコーディング。
        :type charset: str
        """
        self.__email_header = email_header
        self.__charset = charset

    def get_name(self) -> str:
        return self.__email_header.name

    def to_header(self) -> Header:
        return Header(self.__email_header.value, charset=self.__charset)


MimeEmailHeader = Union[AsciiEmailHeader, NonAsciiEmailHeader]


@dataclass(frozen=True)
class TextPlainBody:
    """``text/plain`` パート。"""

    value: str


MimePartT = TypeVar(r"MimePartT", bound=MIMENonMultipart)
"""`MIMENonMultipart` subtype."""


class MimeEncodablePart(Generic[MimePartT], metaclass=ABCMeta):
    """MIME エンコード可能。

    `MimePartT` の具象クラスに対応する MIME エンコード済みコンテンツを返す。
    """

    @abstractmethod
    def encoded_content(self) -> MimePartT:
        """MIMEエンコードされた内容を返す。

        :return: MIMEエンコードされた内容。
        :rtype: str
        """
        ...


class MimeTextPlainPart(MimeEncodablePart[MIMEText]):
    __text_plain_body: TextPlainBody
    __charset: str

    def __init__(self, text_plain_body: TextPlainBody, charset: str) -> None:
        self.__text_plain_body = text_plain_body
        self.__charset = charset

    def encoded_content(self) -> MIMEText:
        return encode_mime_text(
            self.__text_plain_body.value, subtype=r"plain", charset=self.__charset
        )


MimeEmailBody = MimeTextPlainPart


def encode_mime_text(body: str, subtype: str, charset: str) -> MIMEText:
    """`text/*` タイプの MIME コンテンツを生成する。

    :param body: テキストコンテンツ。
    :type body: str
    :param subtype: テキストコンテンツのタイプ。 ``plain/text`` のコンテンツを
        作成するのであれば ``text`` を指定する。
    :type subtype: str
    :param charset: テキストの文字エンコーディング。
    :type charset: str
    :return: ``MimeText``
    :rtype: MIMEText
    """
    # テキストのコンテンツタイプは `text/plain` だが `MIMEText` 内部で `text/` までは
    # 指定されるため、 `plain` の部分のみを指定する。
    return MIMEText(body, _subtype=subtype, _charset=charset)
