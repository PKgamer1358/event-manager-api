# app/core/firebase.py

import firebase_admin
from firebase_admin import credentials, messaging

_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if not _firebase_initialized:
        cred = credentials.Certificate(
            "app/core/firebase-service-account.json"
        )
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True


def send_fcm(token: str, title: str, body: str, sticky: bool = False):
    init_firebase()

    # Android specific config to make it "sticky" (ongoing)
    android_config = messaging.AndroidConfig(
        priority='high',
        notification=messaging.AndroidNotification(
            channel_id='default', # Ensure you have a channel on frontend
            sticky=sticky,        # This makes it non-dismissible
            default_sound=True,
            priority='max' if sticky else 'high'
        )
    )

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        android=android_config,
        token=token,
    )

    messaging.send(message)
