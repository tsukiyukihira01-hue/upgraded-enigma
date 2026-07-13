import threading
import random
from core.engine import TickEngine
from core.graph_map import GraphMap
from db.database import DatabaseManager
from db.repository import Repository
from logic.systems import EconomySystem, MovementSystem
from ui.app import UIApp

def bootstrap_world(repo: Repository, graph: GraphMap):
    print("Generating world...")
    graph.generate_random_network(count=180, avg_degree=3, width=1400, height=900)
    repo.save_map(graph)

    db = repo.db
    with db.conn:
        db.conn.execute("DELETE FROM entities")
        db.conn.execute("DELETE FROM factions")
        # 4 factions
        factions = [(0,"Imperium","#E63946"),(1,"Freeholds","#457B9D"),(2,"Verdant","#2A9D8F"),(3,"Auric","#E9C46A")]
        db.conn.executemany("INSERT INTO factions (id,name,color) VALUES (?,?,?)", factions)
        # seed entities: 1 city + 3 armies per faction
        eid = 1
        nodes = list(graph.nodes.keys())
        for fid in range(4):
            city_node = random.choice(nodes)
            rows = []
            rows.append((eid, city_node, fid, "city", 100, 500.0, 0, None)); eid+=1
            for _ in range(4):
                n = random.choice(nodes)
                rows.append((eid, n, fid, "army", random.randint(30,80), 100.0, 3, None)); eid+=1
            db.bulk_upsert_entities(rows)
    print("World ready")

def main():
    db = DatabaseManager()
    repo = Repository(db)
    graph = GraphMap()

    # rebuild world if empty
    snap = db.fetch_snapshot()
    if not snap["nodes"]:
        bootstrap_world(repo, graph)
    else:
        # reconstruct graph from DB for pathfinding
        for n in snap["nodes"]:
            from core.graph_map import GraphNode
            import json
            graph.add_node(GraphNode(n["id"], n["x"], n["y"], n["type"], json.loads(n["data_json"] or "{}")))
        for e in snap["edges"]:
            graph.add_edge(e["a"], e["b"], e["cost"], bidirectional=False)

    engine = TickEngine(tick_rate_per_sec=4.0)
    economy = EconomySystem(repo)
    movement = MovementSystem(repo, graph)

    engine.register_system(economy)
    engine.register_system(movement)

    # run engine in background thread so UI stays responsive
    engine_thread = threading.Thread(target=engine.run, daemon=True)
    engine_thread.start()

    # UI in main thread (pygame requires main thread)
    app = UIApp(engine, db)
    app.run()

    db.close()

if __name__ == "__main__":
    main()
