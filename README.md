Tick-Based Grand Strategy - Decoupled Architecture
This is a production grade starter for a tick based grand strategy game in Python.

Separation principles
Core Engine knows nothing about UI or DB. It only ticks.
Logic Systems know rules and listen to events. They use Repository, not raw SQL.
DB Layer knows only fast SQLite. No game rules. Optimized for bulk.
UI / Visual Engine only reads snapshots and pushes commands. Never mutates state directly.

Why this wont break
EventBus instead of direct imports prevents circular dependencies
Engine thread and UI thread communicate only via command_queue and DB snapshot
All DB writes go through one transaction per tick using executemany and UPSERT
Graph map is serializable and pathfinding is independent of rendering
Fast bulk SQL tricks used
PRAGMA journal_mode=WAL + synchronous=NORMAL
One BEGIN/COMMIT per tick via with conn:
INSERT ... ON CONFLICT DO UPDATE + executemany
For >500 updates per tick: temp table + join update (fast_bulk_update_by_temp_table)
Indexes on node_id and owner_id
Graph Map
Nodes are provinces or systems with x,y,type. Edges have cost.
Uses adjacency list + A* for movement. Generates organic network via nearest neighbor.

Run
pip install -r requirements.txt
python main.py
Controls: drag to pan, scroll to zoom, hold SPACE to issue random move orders for demo. Click handling can be added in visual_engine.py by pushing move_army commands.

Extend next
Add DiplomacySystem that only reads/writes faction table
Add CombatSystem that resolves battles when multiple factions share node
Replace pygame with pyglet or Godot bridge, no engine change needed
Add save states: copy world.db file, it is already WAL safe
