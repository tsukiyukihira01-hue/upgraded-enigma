import sqlite3
import pathlib
from typing import List, Tuple, Iterable

DB_PATH = pathlib.Path(__file__).parent / "world.db"

class DatabaseManager:
    """
    Handles all SQLite access. No game logic here.
    Optimized for bulk updates: single transaction, prepared statements, WAL.
    """
    def __init__(self, path=DB_PATH):
        self.path = pathlib.Path(path)
        self.conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._apply_pragmas()
        self._init_schema()

    def _apply_pragmas(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA cache_size=-64000;")
        cur.execute("PRAGMA temp_store=MEMORY;")
        cur.execute("PRAGMA foreign_keys=ON;")

    def _init_schema(self):
        schema_file = pathlib.Path(__file__).parent / "schema.sql"
        with open(schema_file, "r") as f:
            self.conn.executescript(f.read())

    def bulk_upsert_nodes(self, rows: List[Tuple]):
        """rows: (id, x, y, type, data_json)"""
        sql = "INSERT OR REPLACE INTO nodes (id,x,y,type,data_json) VALUES (?,?,?,?,?)"
        with self.conn:
            self.conn.executemany(sql, rows)

    def bulk_upsert_edges(self, rows: List[Tuple]):
        sql = "INSERT OR REPLACE INTO edges (a,b,cost) VALUES (?,?,?)"
        with self.conn:
            self.conn.executemany(sql, rows)

    def bulk_upsert_entities(self, rows: Iterable[Tuple]):
        """
        Fastest pattern for grand strategy ticks: one transaction, executemany with UPSERT.
        rows: (id, node_id, owner_id, kind, manpower, wealth, moves_left, target_node)
        """
        sql = """
        INSERT INTO entities (id, node_id, owner_id, kind, manpower, wealth, moves_left, target_node)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          node_id=excluded.node_id,
          owner_id=excluded.owner_id,
          manpower=excluded.manpower,
          wealth=excluded.wealth,
          moves_left=excluded.moves_left,
          target_node=excluded.target_node
        """
        with self.conn:  # single transaction = 10x to 100x faster
            self.conn.executemany(sql, rows)

    def fast_bulk_update_by_temp_table(self, updates: List[Tuple[int, int, int]]):
        """
        Alternative ultra fast path when updating 10k+ rows per tick.
        updates: list of (id, new_node_id, new_manpower)
        Uses temp table + join update which is faster than many individual updates in SQLite.
        """
        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS tmp_updates")
        cur.execute("CREATE TEMP TABLE tmp_updates(id INTEGER PRIMARY KEY, node_id INTEGER, manpower INTEGER)")
        cur.executemany("INSERT INTO tmp_updates VALUES (?,?,?)", updates)
        cur.execute("""
            UPDATE entities SET
              node_id = (SELECT node_id FROM tmp_updates WHERE tmp_updates.id = entities.id),
              manpower = (SELECT manpower FROM tmp_updates WHERE tmp_updates.id = entities.id)
            WHERE id IN (SELECT id FROM tmp_updates)
        """)
        self.conn.commit()

    def fetch_snapshot(self):
        cur = self.conn.cursor()
        nodes = cur.execute("SELECT * FROM nodes").fetchall()
        edges = cur.execute("SELECT * FROM edges").fetchall()
        entities = cur.execute("SELECT * FROM entities").fetchall()
        factions = cur.execute("SELECT * FROM factions").fetchall()
        return {
            "nodes": [dict(r) for r in nodes],
            "edges": [dict(r) for r in edges],
            "entities": [dict(r) for r in entities],
            "factions": [dict(r) for r in factions]
        }

    def close(self):
        self.conn.close()
