from fastapi import BackgroundTasks
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.models import User, Event

def send_email(to_email: str, subject: str, body: str):
    if not settings.SMTP_SERVER or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        print("SMTP settings not configured. Email not sent.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

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
                <li><strong>Location:</strong> {event.location}</li>
            </ul>
            
            <p>We look forward to seeing you there!</p>
            <br>
            <p>Best regards,</p>
            <p>Event Manager Team</p>
        </body>
    </html>
    """
    
    # We'll use this function directly or via background tasks
    send_email(user.email, subject, body)
