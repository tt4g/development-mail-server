import poplib
from email import message_from_bytes
from email.header import decode_header


def _decode_email_header(header):
    decoded = decode_header(header)
    value = r""
    for decoded_bytes, charset in decoded:
        # `email.header.decode_header` は電子メールのヘッダー行の先頭と末尾の
        # 空白文字は削除する。しかし RFC 2822 にある「CRLF を除いて78文字」としたほうが良い
        # というルールに基づいて 78行目から CRLF で改行して複数行で1つのヘッダー値を
        # 記述しているような時は「次の行にヘッダー値が続く場合は末尾の改行コードを無視する」という
        # ルールに基づいて改行文字を削除してくれない。ヘッダー行に改行が出現するとは
        # 考えられないので、改行コードは RFC 2822 のヘッダー値を複数行に記載するためのもので
        # あるとみなして削除する。
        for decoded_byte_line in decoded_bytes.splitlines():
            if charset is None:
                value += decoded_byte_line.decode()
            else:
                value += decoded_byte_line.decode(charset)

    return value


mail_box = poplib.POP3(host=r"127.0.0.1", port=110)
try:
    mail_box.user(r"bar@development-virtual.example.com")
    mail_box.pass_(r"bar")

    # `poplib.POP3.stat` returns `(message count, mailbox size)`
    message_count = mail_box.stat()[0]

    email_separator = r"-" * 80

    # POP3 のメッセージ番号 (message-numbers) は `1` 始まりなので `1`からメッセージ数まで
    # ループする。
    # メッセージ番号が小さい値ほど古いメッセージなので `range(1, message_count + 1)` で
    # 古いメッセージを最初に取得する。
    for message_index in range(1, message_count + 1):
        # `poplib.POP3.retr` returns `(response, [line, ...], octets)``
        lines = mail_box.retr(message_index)[1]
        raw_email = b"\r\n".join(lines)
        parsed_email = message_from_bytes(raw_email)
        print(r"email:", message_index)
        print(email_separator)
        print(r"From:", _decode_email_header(parsed_email[r"From"]))
        print(r"To:", _decode_email_header(parsed_email[r"To"]))
        print(r"Date:", parsed_email[r"Date"])
        print(r"Subject:", _decode_email_header(parsed_email[r"Subject"]))
        for part in parsed_email.walk():
            if part.is_multipart():
                continue
            elif (
                part.get_content_maintype() == r"text"
                and part.get_content_subtype() == r"plain"
            ):
                text: bytes = part.get_payload(
                    decode=True
                )  # .decode(part.get_content_charset())
                content_charset = part.get_content_charset()
                decoded_text = (
                    text.decode(encoding=content_charset, errors=r"ignore")
                    if content_charset is not None
                    else text.decode(encoding=r"ascii", errors=r"ignore")
                )
                print("Text:\n", decoded_text)
            else:
                print(r"Unsupported mail content:", part.get_content_type())
        print(email_separator)

        print()
        print(r"Remove: ", message_index)
        print(mail_box.dele(message_index))
        print()
finally:
    mail_box.quit()
