import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# ... existing code ...
from db_handler import db


def customMailer(recipient_email, subject, body):
    # Fetch SMTP settings from the database
    smtp_host = db.get_value('SMTP_HOST', 'localhost')
    smtp_port = int(db.get_value('SMTP_PORT', '25'))
    smtp_username = db.get_value('SMTP_USERNAME', '')
    smtp_password = db.get_value('SMTP_PASSWORD', '')
    smtp_security = db.get_value('SMTP_SECURITY', 'TLS')

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    try:
        # Set up the SMTP connection based on the security setting
        if smtp_security == 'SSL':
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            if smtp_security == 'TLS':
                server.starttls()

        # Login if credentials are provided
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        # Send the email
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"
