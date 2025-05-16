
import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASS
import logging

def send_email(to, subject, body, bcc=None, sender="your_email@example.com"):
    logging.info("Email sending is currently disabled. Outputting to console instead.")
    print("\n[EMAIL MOCK] Subject:", subject)
    print("Body:\n", body)

