"""
Email sender using SendGrid
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from config import SENDGRID_API_KEY, SENDER_EMAIL, RECIPIENT_EMAIL


class EmailSender:
    """Sends emails using SendGrid"""

    def __init__(self):
        if not SENDGRID_API_KEY:
            raise ValueError("SENDGRID_API_KEY environment variable not set")

        self.client = SendGridAPIClient(SENDGRID_API_KEY)
        self.sender_email = SENDER_EMAIL
        self.recipient_email = RECIPIENT_EMAIL

    def send_email(self, subject: str, html_content: str) -> bool:
        """
        Send an email

        Args:
            subject: Email subject
            html_content: HTML email body

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            message = Mail(
                from_email=Email(self.sender_email),
                to_emails=To(self.recipient_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.client.send(message)

            # Print detailed response information for debugging
            print(f"\n📬 SendGrid Response Details:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response Body: {response.body}")
            print(f"  Response Headers: {response.headers}")

            if response.status_code in [200, 201, 202]:
                print(f"\n✓ Email sent successfully!")
                print(f"  From: {self.sender_email}")
                print(f"  To: {self.recipient_email}")
                print(f"  Subject: {subject}")
                print(f"\n⚠️  IMPORTANT: Check your spam folder if you don't see the email!")
                print(f"  Gmail often marks automated emails as spam initially.")
                print(f"  If it's in spam, mark it as 'Not Spam' to receive future emails.")
                return True
            else:
                print(f"\n✗ Email send failed with status code: {response.status_code}")
                print(f"  This usually means there's an issue with SendGrid configuration.")
                return False

        except Exception as e:
            print(f"✗ Error sending email: {e}")
            return False

    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        subject = "NYC Movie Screenings - Test Email"
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            max-width: 600px;
            margin: 0 auto;
        }
        h1 {
            color: #e50914;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🎬 Test Email</h1>
    <p>This is a test email from your NYC Movie Screenings automation system.</p>
    <p>If you're receiving this, your email configuration is working correctly!</p>
    <p><strong>Next steps:</strong></p>
    <ul>
        <li>The system will automatically send you weekly screening digests every Monday at 8am EST</li>
        <li>Emails will include special screenings, premieres, Q&As, and repertory cinema</li>
        <li>You don't need to do anything - it's fully automated!</li>
    </ul>
</div>
</body>
</html>
"""
        return self.send_email(subject, html_content)
