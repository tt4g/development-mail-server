from dataclasses import dataclass
from typing import Collection, Optional

from ._email import EmailAddress, Subject, TextPlainBody


@dataclass(frozen=True)
class SmtpServerConfig:
    """SMTPサーバー設定。"""

    host: str
    """ホスト名。"""
    port: int
    """ポート番号。"""
    connect_timeout: int
    """コネクションタイムアウト（秒）。"""


@dataclass(frozen=True)
class SmtpLoginCredentials:
    """SMTP認証情報。"""

    user: str
    """ユーザー名。"""
    password: str
    """パスワード。"""


@dataclass(frozen=True)
class SendEmail:
    """送信する電子メール。"""

    charset: str
    """電子メールの文字エンコーディング。"""

    sender_from: EmailAddress
    to: Collection[EmailAddress]
    cc: Collection[EmailAddress]
    bcc: Collection[EmailAddress]
    subject: Subject
    body: TextPlainBody


@dataclass(frozen=True)
class SendSmtpCommand:
    """SMTPプロトコルによるメール送信。"""

    smtp_server_config: SmtpServerConfig
    smtp_login_credentials: Optional[SmtpLoginCredentials]
    send_email: SendEmail
