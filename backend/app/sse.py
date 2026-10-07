import asyncio
import json
from collections import defaultdict
from typing import Dict, Set

from agent.events import subscribe, unsubscribe, Event
from backend.app.db import get_events_since

class StreamManager:
    def __init__(self):
        # project_id -> list of (queue, loop)
        self.listeners: Dict[str, Set[tuple]] = defaultdict(set)
        subscribe(self.handle_new_event)

    def handle_new_event(self, event: Event):
        if event.project_id in self.listeners:
            for queue, loop in list(self.listeners[event.project_id]):
                try:
                    # thread-safe push since handle_new_event is called from worker thread
                    loop.call_soon_threadsafe(queue.put_nowait, event)
                except Exception:
                    pass

    async def event_generator(self, project_id: str, last_event_id: int):
        # 1. Yield caught-up events from DB
        db_events = get_events_since("data/rerun.db", project_id, last_event_id)
        for ev_dict in db_events:
            last_event_id = ev_dict["id"]
            yield f"id: {last_event_id}\nevent: message\ndata: {json.dumps(ev_dict)}\n\n"

        # 2. Live event stream
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        listener_tuple = (queue, loop)
        self.listeners[project_id].add(listener_tuple)
        
        try:
            while True:
                # Wait for the next event
                ev: Event = await queue.get()
                if ev.id > last_event_id:
                    # serialize
                    ev_dict = ev.model_dump()
                    yield f"id: {ev.id}\nevent: message\ndata: {json.dumps(ev_dict)}\n\n"
                    last_event_id = ev.id
        except asyncio.CancelledError:
            pass
        finally:
            if listener_tuple in self.listeners[project_id]:
                self.listeners[project_id].remove(listener_tuple)

stream_manager = StreamManager()
