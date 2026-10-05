import json
from django.conf import settings

def send_push_notification(user_id, title, body, url='/'):
    """
    Sends a Web Push notification to all active subscriptions of a user.
    Requires: pip install pywebpush
    """
    from .models import PushSubscription
    subscriptions = PushSubscription.objects.filter(user_id=user_id)
    
    if not subscriptions.exists():
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print("\n[PUSH NOTIFICATION] Error: 'pywebpush' library not found.")
        print("To enable background notifications (app closed), run: pip install pywebpush\n")
        return

    # You should generate your own VAPID keys
    # Run: web-push generate-vapid-keys
    VAPID_PRIVATE_KEY = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    VAPID_CLAIMS = {
        "sub": "mailto:admin@garderienova.com"
    }

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as ex:
            print(f"Push error: {ex}")
            # If subscription expired, delete it
            if "410" in str(ex) or "404" in str(ex):
                sub.delete()
        except Exception as e:
            print(f"Push failed: {e}")
