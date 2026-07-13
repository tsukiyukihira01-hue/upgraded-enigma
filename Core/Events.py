from collections import defaultdict
from typing import Callable, Dict, List

class EventBus:
    """Decoupled pub sub. Engine, Logic, UI never call each other directly."""
    def __init__(self):
        self._subs: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event_type: str, fn: Callable):
        self._subs[event_type].append(fn)

    def off(self, event_type: str, fn: Callable):
        if fn in self._subs[event_type]:
            self._subs[event_type].remove(fn)

    def emit(self, event_type: str, payload: dict = None):
        payload = payload or {}
        for fn in list(self._subs[event_type]):
            fn(payload)
