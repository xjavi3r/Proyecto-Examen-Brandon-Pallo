from threading import Thread

import requests
from django.conf import settings
from django.utils import timezone


def enviar_evento_async(action, description, payload, title=None):
    timestamp = timezone.now().isoformat()
    event = {
        "source": settings.EVENT_SOURCE,
        "entity": "producto",
        "action": action,
        "type": action,
        "timestamp": timestamp,
        "title": title or f"Producto {action.lower()}",
        "description": description,
        "payload": payload,
    }
    Thread(target=_post_event, args=(event,), daemon=True).start()


def _post_event(event):
    try:
        requests.post(settings.EVENT_MANAGER_URL, json=event, timeout=2)
    except requests.RequestException:
        pass
