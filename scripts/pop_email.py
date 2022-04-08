import email
import poplib


def decode_header(header):
    decoded_bytes, charset = email.header.decode_header(header)[0]
    if charset is None:
        return str(decoded_bytes)
    else:
        return decoded_bytes.decode(charset)


mail_box = poplib.POP3(host=r"127.0.0.1", port=110)
mail_box.user(r"bar@development-virtual.example.com")
mail_box.pass_(r"bar")

message_count = len(mail_box.list()[1])

email_separator = r"-" * 80

for i in range(message_count):
    raw_email = b"\n".join(mail_box.retr(i + 1)[1])
    parsed_email = email.message_from_bytes(raw_email)
    print(rf"email: {i}")
    print(email_separator)
    print(r"From:", parsed_email[r"From"])
    print(r"To:", parsed_email[r"To"])
    print(r"Date:", parsed_email[r"Date"])
    print(r"Subject:", decode_header(parsed_email[r"Subject"]))
    for part in parsed_email.walk():
        if part.is_multipart():
            continue
        elif part.get_content_maintype() == r"text":
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
