import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.header import Header
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Collection, Iterable, NoReturn, Optional

from email_test._email import (
    EmailAddress,
    EmailHeader,
    MimeEmailAddress,
    MimeEmailBody,
    MimeEmailHeader,
    MimeTextPlainPart,
    NonAsciiEmailAddress,
    NonAsciiEmailHeader,
    Subject,
    TextPlainBody,
    format_recipient_header,
)
from email_test._smtp import (
    SendEmail,
    SendSmtpCommand,
    SmtpLoginCredentials,
    SmtpServerConfig,
)


@dataclass(frozen=True)
class SendMimeEmail:
    sender_from: MimeEmailAddress
    to: Collection[MimeEmailAddress]
    cc: Collection[MimeEmailAddress]
    bcc: Collection[MimeEmailAddress]
    headers: Collection[MimeEmailHeader]
    part: Collection[MimeEmailBody]


def send_smtp_email(send_smtp_command: SendSmtpCommand):
    validate_send_email(send_email=send_smtp_command.send_email)

    send_mime_email = convert_send_mime_email(send_email=send_smtp_command.send_email)
    message = convert_email_message(send_mime_email=send_mime_email)

    smtp_server_config: SmtpServerConfig = send_smtp_command.smtp_server_config
    smtp_login_credentials: Optional[
        SmtpLoginCredentials
    ] = send_smtp_command.smtp_login_credentials

    try:
        # Send the message via our own SMTP server.
        with smtplib.SMTP(
            host=smtp_server_config.host,
            port=smtp_server_config.port,
            timeout=smtp_server_config.connect_timeout,
        ) as smtp:
            if smtp_login_credentials is not None:
                auth = smtp.login(
                    user=smtp_login_credentials.user,
                    password=smtp_login_credentials.password,
                )
                print(auth)

            smtp.send_message(message)
    except smtplib.SMTPException as err:
        print(r"Failed to send email.", err)


def validate_send_email(send_email: SendEmail) -> Optional[NoReturn]:
    if all(
        len(recipient) < 1
        for recipient in (send_email.to, send_email.cc, send_email.bcc)
    ):
        raise Exception(r"No recipient specified.")

    return None


def convert_send_mime_email(send_email: SendEmail) -> SendMimeEmail:
    charset = send_email.charset

    def _to_mime_email_address(email_address: EmailAddress) -> MimeEmailAddress:
        return NonAsciiEmailAddress(email_address=email_address, charset=charset)

    def _to_mime_email_addresses(
        email_addresses: Iterable[EmailAddress],
    ) -> Collection[MimeEmailAddress]:
        return tuple(
            _to_mime_email_address(email_address=email_address)
            for email_address in email_addresses
        )

    sender_from = _to_mime_email_address(send_email.sender_from)
    to = _to_mime_email_addresses(send_email.to)
    cc = _to_mime_email_addresses(send_email.cc)
    bcc = _to_mime_email_addresses(send_email.bcc)

    subject_header = EmailHeader(name=r"Subject", value=send_email.subject.value)
    headers = [NonAsciiEmailHeader(email_header=subject_header, charset=charset)]

    part = (MimeTextPlainPart(text_plain_body=send_email.body, charset=charset),)

    return SendMimeEmail(
        sender_from=sender_from, to=to, cc=cc, bcc=bcc, headers=headers, part=part
    )


def convert_email_message(send_mime_email: SendMimeEmail) -> Message:
    def _create_message(part: Collection[MimeEmailBody]) -> Message:
        part_len = len(part)
        if part_len == 0:
            # create empty `text/plain`.
            return MIMEText(r"", r"plain")
        elif part_len == 1:
            return next(iter(part)).encoded_content()

        #  create `multipart/alternative`.
        message = MIMEMultipart(r"alternative")
        for p in part:
            message.attach(p.encoded_content())

        return message

    def _set_recipient_header(
        message: Message,
        name: str,
        mime_email_addresses: Collection[MimeEmailAddress],
    ) -> None:
        if len(mime_email_addresses) == 0:
            return

        value = format_recipient_header(mime_email_addresses=mime_email_addresses)
        message.add_header(name, value)

    def _set_headers(
        message: Message, headers: Collection[MimeEmailHeader]
    ) -> None:
        for header in headers:
            converted: Header = header.to_header()
            message.add_header(header.get_name(), converted.encode())

    message = _create_message(part=send_mime_email.part)
    message[r"From"] = send_mime_email.sender_from.to_formatted().value
    _set_recipient_header(
        message=message, name=r"To", mime_email_addresses=send_mime_email.to
    )
    _set_recipient_header(
        message=message, name=r"Cc", mime_email_addresses=send_mime_email.cc
    )
    _set_recipient_header(
        message=message, name=r"Bcc", mime_email_addresses=send_mime_email.bcc
    )
    _set_headers(message=message, headers=send_mime_email.headers)

    return message


if __name__ == r"__main__":
    smtp_server_config = SmtpServerConfig(
        host=r"127.0.0.1", port=25, connect_timeout=1000
    )
    smtp_login_credentials = SmtpLoginCredentials(
        user=r"foo@development-virtual.example.com", password=r"foo"
    )
    send_email = SendEmail(
        charset=r"utf-8",
        sender_from=EmailAddress(
            address=r"foo@development-virtual.example.com", name=r"ふうー"
        ),
        to=[
            EmailAddress(address=r"bar@development-virtual.example.com", name=r"バー"),
        ],
        cc=[],
        bcc=[],
        subject=Subject(
            value=(
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                r"日本語メール日本語メール日本語メール日本語メール日本語メール日本語メール"
                )),
        body=TextPlainBody(
            (
                f"""日本語を含む電子メール送信の送信テスト。

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            )
        ),
    )
    send_smtp_command = SendSmtpCommand(
        smtp_server_config=smtp_server_config,
        smtp_login_credentials=smtp_login_credentials,
        send_email=send_email,
    )
    send_smtp_email(send_smtp_command=send_smtp_command)
