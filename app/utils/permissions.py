from app.models import User, Event

def can_manage_event(user: User, event: Event) -> bool:
    if user.is_super_admin:
        return True
    if user.is_admin and event.created_by == user.id:
        return True
    return False