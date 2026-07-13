PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;
PRAGMA temp_store=MEMORY;

CREATE TABLE IF NOT EXISTS nodes (
  id INTEGER PRIMARY KEY,
  x REAL NOT NULL,
  y REAL NOT NULL,
  type TEXT NOT NULL,
  data_json TEXT
);

CREATE TABLE IF NOT EXISTS edges (
  a INTEGER NOT NULL,
  b INTEGER NOT NULL,
  cost REAL NOT NULL,
  PRIMARY KEY (a,b)
);

CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY,
  node_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  manpower INTEGER DEFAULT 0,
  wealth REAL DEFAULT 0,
  moves_left INTEGER DEFAULT 1,
  target_node INTEGER,
  FOREIGN KEY(node_id) REFERENCES nodes(id)
);

CREATE TABLE IF NOT EXISTS factions (
  id INTEGER PRIMARY KEY,
  name TEXT,
  color TEXT,
  treasury REAL DEFAULT 1000
);

CREATE INDEX IF NOT EXISTS idx_entities_node ON entities(node_id);
CREATE INDEX IF NOT EXISTS idx_entities_owner ON entities(owner_id);
