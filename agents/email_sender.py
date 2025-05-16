
import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASS
import logging

def send_email(to, subject, body, bcc=None, sender="your_email@example.com"):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    recipients = [to] + (bcc if bcc else [])

    try:
        with smtplib.SMTP("smtp.mailserver.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(sender, recipients, msg.as_string())
        logging.info("Email successfully sent to: %s", ', '.join(bcc))
    except Exception as e:
        logging.error("Failed to send email: %s", str(e))
        raise
