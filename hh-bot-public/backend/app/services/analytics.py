from __future__ import annotations

import logging
from typing import Any


_LOGGER = logging.getLogger("analytics")
_KNOWN_EVENTS = {
    "payment_initiated",
    "payment_succeeded",
    "payment_failed",
}


def track_event(event_name: str, **payload: Any) -> None:
    """Emit lightweight analytics events through structured logging."""
    if event_name not in _KNOWN_EVENTS:
        _LOGGER.debug("analytics skip unknown event %s", event_name)
        return
    _LOGGER.info("analytics event %s %s", event_name, payload)
