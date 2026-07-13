"""
Game rules isolated from engine. Change these without touching engine or UI.
"""
COMBAT_POWER = {
    "militia": 1,
    "infantry": 3,
    "cavalry": 5,
    "army": 10
}

def can_traverse(node_type: str, entity_kind: str) -> bool:
    if node_type == "sea" and entity_kind not in ("fleet", "army_with_fleet"):
        return False
    return True

def upkeep_cost(entity: dict) -> float:
    return entity.get("manpower", 0) * 0.1
