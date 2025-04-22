import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Replace with actual credentials or use environment variables
SENDER_EMAIL = "vinniesharma965@gmail.com"
SENDER_PASSWORD = "tlns lgtv yakb muer"
RECEIVER_EMAIL = "vinniesharma22@gmail.com"

def send_email_alert(subject, plain_message, attachment_path=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        # Attach plain text message
        text_part = MIMEText(plain_message, "plain")
        msg.attach(text_part)

        # Attach file if path provided
        if attachment_path:
            with open(attachment_path, "rb") as f:
                file_attachment = MIMEApplication(f.read(), _subtype="octet-stream")
                file_attachment.add_header("Content-Disposition", "attachment", filename=attachment_path.split("/")[-1])
                msg.attach(file_attachment)

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully.")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")