import time
from collections import deque
from .events import EventBus

class TickEngine:
    """
    Pure tick orchestrator. Knows nothing about pygame, sqlite, or game rules.
    It only advances tick counter, drains command queue, and calls systems.
    """
    def __init__(self, tick_rate_per_sec: float = 2.0):
        self.tick: int = 0
        self.tick_rate = tick_rate_per_sec
        self.systems = []
        self.command_queue = deque()
        self.bus = EventBus()
        self.running = False

    def register_system(self, system):
        """system must implement on_tick(tick) and optional bind(bus, engine)"""
        if hasattr(system, "bind"):
            system.bind(self.bus, self)
        self.systems.append(system)

    def push_command(self, cmd: dict):
        """
        cmd example: {"type": "move_army", "army_id": 5, "to_node": 12}
        UI pushes here. Logic systems listen via bus.
        """
        self.command_queue.append(cmd)

    def step(self):
        while self.command_queue:
            cmd = self.command_queue.popleft()
            self.bus.emit(cmd.get("type"), cmd)

        for sys in self.systems:
            sys.on_tick(self.tick)

        self.bus.emit("tick_completed", {"tick": self.tick})
        self.tick += 1

    def run(self, max_ticks: int = None):
        self.running = True
        while self.running:
            start = time.time()
            self.step()
            if max_ticks is not None and self.tick >= max_ticks:
                break
            elapsed = time.time() - start
            sleep_for = max(0, (1.0 / self.tick_rate) - elapsed)
            if sleep_for:
                time.sleep(sleep_for)

    def stop(self):
        self.running = False
