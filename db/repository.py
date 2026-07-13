from typing import Dict, List
from db.database import DatabaseManager

class Repository:
    """
    Logic layer talks to this, not directly to sqlite.
    This keeps SQL bulk optimization isolated from game rules.
    """
    def __init__(self, db: DatabaseManager):
        self.db = db

    def save_map(self, graph_map):
        node_rows, edge_rows = graph_map.to_rows()
        self.db.bulk_upsert_nodes(node_rows)
        self.db.bulk_upsert_edges(edge_rows)

    def load_snapshot(self):
        return self.db.fetch_snapshot()

    def commit_tick(self, dirty_entities: List[Dict]):
        if not dirty_entities:
            return
        rows = [
            (e["id"], e["node_id"], e["owner_id"], e["kind"],
             e["manpower"], e["wealth"], e.get("moves_left", 1), e.get("target_node"))
            for e in dirty_entities
        ]
        self.db.bulk_upsert_entities(rows)
