from collections import defaultdict

class EconomySystem:
    """Example tick system. Pure logic. No UI, no SQL."""
    def __init__(self, repo):
        self.repo = repo
        self.state = {"entities": {}, "factions": {}}
        self.dirty = {}

    def bind(self, bus, engine):
        self.bus = bus
        self.engine = engine
        bus.on("tick_completed", self.on_snapshot_refresh)
        # initial load
        snap = self.repo.load_snapshot()
        for e in snap["entities"]:
            self.state["entities"][e["id"]] = e

    def on_snapshot_refresh(self, payload):
        # optionally refresh from DB every N ticks, here we keep in memory
        pass

    def on_tick(self, tick):
        # income logic
        income_by_faction = defaultdict(float)
        for eid, ent in self.state["entities"].items():
            if ent["kind"] == "city":
                ent["wealth"] += 5.0
                ent["manpower"] += 2
                income_by_faction[ent["owner_id"]] += 5.0
                self.dirty[eid] = ent
        if self.dirty:
            self.repo.commit_tick(list(self.dirty.values()))
            self.dirty.clear()

class MovementSystem:
    """Handles graph movement. Uses GraphMap for pathfinding."""
    def __init__(self, repo, graph_map):
        self.repo = repo
        self.map = graph_map
        self.entities = {}
        self.dirty = {}

    def bind(self, bus, engine):
        self.bus = bus
        bus.on("move_army", self.on_move_command)
        snap = self.repo.load_snapshot()
        for e in snap["entities"]:
            self.entities[e["id"]] = e

    def on_move_command(self, cmd):
        eid = cmd["army_id"]
        to_node = cmd["to_node"]
        if eid in self.entities:
            self.entities[eid]["target_node"] = to_node
            self.entities[eid]["moves_left"] = 3
            self.dirty[eid] = self.entities[eid]

    def on_tick(self, tick):
        moved = []
        for eid, ent in list(self.entities.items()):
            if ent.get("target_node") is None:
                continue
            if ent.get("moves_left", 0) <= 0:
                continue
            cur = ent["node_id"]
            tgt = ent["target_node"]
            if cur == tgt:
                ent["target_node"] = None
                continue
            path = self.map.shortest_path(cur, tgt)
            if path and len(path) > 1:
                ent["node_id"] = path[1]
                ent["moves_left"] -= 1
                moved.append(ent)
                self.dirty[eid] = ent
                if ent["node_id"] == tgt:
                    ent["target_node"] = None
        if self.dirty:
            self.repo.commit_tick(list(self.dirty.values()))
            # use ultra fast temp table path if > 500 moves
            if len(moved) > 500:
                updates = [(e["id"], e["node_id"], e["manpower"]) for e in moved]
                self.repo.db.fast_bulk_update_by_temp_table(updates)
            self.dirty.clear()
