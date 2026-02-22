"""Event bus — publish/subscribe for extension communication."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Platform-level events
EVENTS = {
    "user.created",
    "user.login",
    "user.deleted",
    "tenant.created",
    "tenant.deleted",
    "payment.succeeded",
    "payment.failed",
    "subscription.created",
    "subscription.cancelled",
    "extension.activated",
    "extension.deactivated",
    "extension.installed",
    "extension.uninstalled",
}


class EventBus:
    """Async publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        """Subscribe a handler to an event."""
        self._subscribers[event].append(handler)
        logger.debug("Subscribed %s to event '%s'", handler.__qualname__, event)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        """Unsubscribe a handler from an event."""
        try:
            self._subscribers[event].remove(handler)
        except ValueError:
            pass

    async def publish(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Publish an event to all subscribers."""
        handlers = self._subscribers.get(event, [])
        if not handlers:
            return

        payload = payload or {}
        logger.debug("Publishing event '%s' to %d handler(s)", event, len(handlers))

        for handler in handlers:
            try:
                result = handler(payload)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Error in event handler %s for event '%s'", handler.__qualname__, event)

    def publish_sync(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Synchronous publish — runs handlers synchronously (no async support)."""
        handlers = self._subscribers.get(event, [])
        payload = payload or {}
        for handler in handlers:
            try:
                handler(payload)
            except Exception:
                logger.exception("Error in sync event handler %s", handler.__qualname__)

    def clear(self) -> None:
        """Clear all subscribers (useful for testing)."""
        self._subscribers.clear()


# Singleton
event_bus = EventBus()
