from app.core.firebase import send_fcm

def send_push_notification(fcm_token: str, title: str, body: str, sticky: bool = False):
    send_fcm(
        token=fcm_token,
        title=title,
        body=body,
        sticky=sticky
    )
