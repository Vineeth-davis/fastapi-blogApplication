"""
Notifications module for Server-Sent Events (SSE).

Provides a singleton notifications manager and the SSE router.
"""

from app.notifications.manager import notifications_manager
from app.notifications.routes import router

__all__ = ["notifications_manager", "router"]


