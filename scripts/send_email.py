import smtplib
from email.message import EmailMessage

message = EmailMessage()
message[r"Subject"] = r"Test email"
message[r"From"] = r"foo@development-virtual.example.com"
message[r"To"] = r"bar@development-virtual.example.com"
message.set_content(r"This is test e-mail.")

# Send the message via our own SMTP server.
with smtplib.SMTP(host=r"127.0.0.1", port=25) as smtp:
    print(smtp.login(user=r"foo@development-virtual.example.com", password=r"foo"))
    smtp.send_message(message)
