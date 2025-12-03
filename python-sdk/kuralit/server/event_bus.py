"""Event bus for broadcasting events to dashboard clients."""

import asyncio
import inspect
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents an event to be broadcast."""
    
    event_type: str
    session_id: Optional[str]
    timestamp: float
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": "event",
            "event_type": self.event_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventBus:
    """Event bus for broadcasting events to subscribers.
    
    This class manages event publishing and subscription for real-time
    dashboard updates. Events are broadcast to all subscribed callbacks.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers: List[Callable[[Event], None]] = []
        self._lock = asyncio.Lock()
        self._event_count = 0
        
    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Subscribe to events.
        
        Args:
            callback: Async function that will be called for each event.
                     Signature: async def callback(event: Event) -> None
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.info(f"EventBus: New subscriber added. Total subscribers: {len(self._subscribers)}")
        else:
            logger.warning("EventBus: Attempted to subscribe with existing callback")
    
    def unsubscribe(self, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.info(f"EventBus: Subscriber removed. Total subscribers: {len(self._subscribers)}")
        else:
            logger.warning("EventBus: Attempted to unsubscribe with non-existent callback")
    
    async def publish(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event_type: Type of event (e.g., 'message_received', 'agent_response')
            session_id: Optional session ID associated with the event
            data: Optional event data dictionary
        """
        if data is None:
            data = {}
        
        event = Event(
            event_type=event_type,
            session_id=session_id,
            timestamp=time.time(),
            data=data
        )
        
        self._event_count += 1
        
        # Broadcast to all subscribers
        if self._subscribers:
            async with self._lock:
                # Create a copy of subscribers list to avoid modification during iteration
                subscribers_copy = self._subscribers.copy()
            
            logger.info(f"EventBus: Broadcasting to {len(subscribers_copy)} subscribers for event '{event_type}' (session={session_id})")
            
            # Call all subscribers concurrently
            tasks = []
            for i, callback in enumerate(subscribers_copy):
                try:
                    # Try calling as async first (all our callbacks are async)
                    logger.debug(f"EventBus: Calling subscriber {i} for event '{event_type}'")
                    coro = callback(event)
                    if asyncio.iscoroutine(coro):
                        tasks.append((i, coro))
                        logger.info(f"EventBus: Subscriber {i}: async callback registered (event='{event_type}')")
                    else:
                        # Not a coroutine, try sync
                        logger.warning(f"EventBus: Subscriber {i}: callback didn't return coroutine, treating as sync")
                        task = asyncio.create_task(
                            asyncio.to_thread(callback, event)
                        )
                        tasks.append((i, task))
                except TypeError as e:
                    # Callback might be sync, try in thread
                    logger.warning(f"EventBus: Subscriber {i}: TypeError calling callback, treating as sync: {e}")
                    try:
                        task = asyncio.create_task(
                            asyncio.to_thread(callback, event)
                        )
                        tasks.append((i, task))
                    except Exception as thread_error:
                        logger.error(f"EventBus: Error creating thread task for subscriber {i}: {thread_error}", exc_info=True)
                except Exception as e:
                    logger.error(f"EventBus: Error calling subscriber {i}: {e}", exc_info=True)
            
            # Wait for all callbacks to complete (or fail)
            if tasks:
                # Extract just the tasks for gather
                task_list = [task for _, task in tasks]
                results = await asyncio.gather(*task_list, return_exceptions=True)
                # Log any exceptions
                for (idx, _), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"EventBus: Subscriber {idx} raised exception: {result}", exc_info=True)
                    else:
                        logger.debug(f"EventBus: Subscriber {idx} completed successfully")
        
        if self._subscribers:
            logger.info(f"EventBus: Published event '{event_type}' (session={session_id}, subscribers={len(self._subscribers)})")
        else:
            logger.debug(f"EventBus: Published event '{event_type}' (session={session_id}, no subscribers)")
    
    def get_subscriber_count(self) -> int:
        """Get number of active subscribers."""
        return len(self._subscribers)
    
    def get_event_count(self) -> int:
        """Get total number of events published."""
        return self._event_count


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance.
    
    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        logger.info("EventBus: Global event bus instance created")
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _event_bus
    _event_bus = None
    logger.info("EventBus: Global event bus reset")

