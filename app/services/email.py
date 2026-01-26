from fastapi import BackgroundTasks
import requests
from app.config import settings
from app.models import User, Event

def send_email(to_email: str, subject: str, html_content: str):
    """
    Sends an email using Brevo (Sendinblue) API v3.
    Use this to bypass port blocking on Render.
    """
    if not settings.BREVO_API_KEY:
        print("❌ Brevo API key not found. Email not sent.")
        return

    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": "Event Manager",
            "email": settings.SMTP_FROM_EMAIL if settings.SMTP_FROM_EMAIL else "no-reply@eventmanager.com"
        },
        "to": [
            {
                "email": to_email,
                "name": to_email.split("@")[0]
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"✅ Email sent successfully to {to_email} (via Brevo)")
        else:
            print(f"❌ Failed to send email via Brevo: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception sending email via Brevo: {e}")

def send_registration_confirmation(user: User, event: Event):
    subject = f"Registration Confirmed: {event.title}"
    
    body = f"""
    <html>
        <body>
            <h2>Hello {user.first_name},</h2>
            <p>You have successfully registered for <strong>{event.title}</strong>.</p>
            
            <h3>Event Details:</h3>
            <ul>
                <li><strong>Date:</strong> {event.start_time.strftime('%Y-%m-%d')}</li>
                <li><strong>Time:</strong> {event.start_time.strftime('%I:%M %p')}</li>
                <li><strong>Location:</strong> {event.venue}</li>
            </ul>
            
            <p>We look forward to seeing you there!</p>
            <br>
            <p>Best regards,</p>
            <p>Event Manager Team</p>
        </body>
    </html>
    """
    
    # Send using Brevo
    send_email(user.email, subject, body)
