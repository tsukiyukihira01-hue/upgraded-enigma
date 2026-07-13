import threading
import time
from db.database import DatabaseManager
from ui.visual_engine import VisualEngine

class UIApp:
    """
    UI layer. Never writes game logic. Only reads DB snapshot and pushes commands to engine queue.
    Runs in main thread, engine runs in background thread.
    """
    def __init__(self, engine, db: DatabaseManager):
        self.engine = engine
        self.db = db
        self.visual = VisualEngine()
        self.selected_army = None

    def run(self):
        running = True
        last_snapshot_time = 0
        snapshot = self.db.fetch_snapshot()

        while running:
            running = self.visual.handle_input()

            # refresh snapshot every 0.15 sec to avoid locking DB too much
            now = time.time()
            if now - last_snapshot_time > 0.15:
                snapshot = self.db.fetch_snapshot()
                last_snapshot_time = now

            # example input: press SPACE to issue random move for demo
            # In real game you would click node -> emit command
            keys = __import__("pygame").key.get_pressed()
            if keys[__import__("pygame").K_SPACE]:
                # find first army and random target
                if snapshot["entities"] and snapshot["nodes"]:
                    import random
                    army = random.choice(snapshot["entities"])
                    target = random.choice(snapshot["nodes"])
                    self.engine.push_command({"type": "move_army", "army_id": army["id"], "to_node": target["id"]})

            self.visual.draw(snapshot)

        self.visual.quit()
        self.engine.stop()
