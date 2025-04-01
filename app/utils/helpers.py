import os, smtplib, random, string

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def format_response(data):
    # Helper to format API responses consistently
    return {"data": data, "status": "success"}


def send_verification_email(email: str, token: str):
    verification_link = f"http://localhost:8000/api/auth/verify/{token}"

    message = f"Subject: Verify Your Email\n\nClick the link to verify your email: {verification_link}"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, message)
    except Exception as e:
        print(f"Error sending email: {e}")

def generate_random_id():
    # Generate 10 random alphanumeric characters
    return ''.join(random.choices("ABCDEF" + string.digits, k=10))