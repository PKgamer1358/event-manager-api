import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure we can import from app
sys.path.append(os.getcwd())

try:
    from app.config import settings
except ImportError:
    print("Error: Could not import settings. Make sure you are running this from the root directory (event-manager-api).")
    print("Usage: python check_email_config.py")
    sys.exit(1)

def test_email_configuration():
    print("--- Checking Email Configuration ---")
    
    server = settings.SMTP_SERVER
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    from_email = settings.SMTP_FROM_EMAIL

    print(f"SMTP Server: {server}")
    print(f"SMTP Port: {port}")
    print(f"Username: {username}")
    print(f"From Email: {from_email}")
    print(f"Password Configured: {'Yes' if password else 'No'}")

    if not all([server, port, username, password, from_email]):
        print("\n❌ Error: One or more SMTP settings are missing in your .env file.")
        return

    print("\nAttempting to connect to SMTP server...")
    
    try:
        # 1. Connect
        smtp = smtplib.SMTP(server, port)
        smtp.set_debuglevel(1)  # Show communication with server
        print("✅ Connected to server.")

        # 2. Start TLS
        smtp.starttls()
        print("✅ TLS Session started.")

        # 3. Login
        print("Attempting login...")
        smtp.login(username, password)
        print("✅ Login successful.")

        # 4. Send Test Email
        print("Sending test email...")
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = username  # Send to self for testing
        msg['Subject'] = "Event Manager - SMTP Test"
        msg.attach(MIMEText("If you are reading this, your email configuration is working correctly!", 'plain'))

        smtp.send_message(msg)
        print(f"✅ Test email sent to {username}")

        smtp.quit()
        print("\n🎉 SUCCESS: Email configuration is valid.")

    except smtplib.SMTPAuthenticationError:
        print("\n❌ AUTHENTICATION ERROR: Login failed.")
        print("Check your username and password.")
        print("If using Gmail, make sure you are using an **App Password**, not your login password.")
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_email_configuration()
