import pygame
import math

COLORS = {
    "plains": (170, 190, 140),
    "hills": (130, 130, 110),
    "forest": (60, 110, 70),
    "city": (220, 200, 100),
    "port": (90, 140, 200),
    "edge": (80, 80, 80),
    "faction": [(230, 50, 50), (50, 120, 230), (50, 200, 120), (230, 180, 50)]
}

class VisualEngine:
    """
    Visual engine only. No logic, no DB writes. Reads snapshot dict.
    Draws graph network map with pan and zoom. Can be swapped for Godot, pyglet, etc.
    """
    def __init__(self, width=1280, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Grand Strategy Graph Map")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 11)
        self.offset = [0, 0]
        self.zoom = 1.0
        self.dragging = False
        self.last_mouse = (0,0)

    def world_to_screen(self, x, y):
        return (x * self.zoom + self.offset[0], y * self.zoom + self.offset[1])

    def handle_input(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    self.dragging = True
                    self.last_mouse = ev.pos
                if ev.button == 4:
                    self.zoom = min(2.5, self.zoom * 1.1)
                if ev.button == 5:
                    self.zoom = max(0.25, self.zoom * 0.9)
            if ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 1:
                    self.dragging = False
            if ev.type == pygame.MOUSEMOTION and self.dragging:
                dx = ev.pos[0] - self.last_mouse[0]
                dy = ev.pos[1] - self.last_mouse[1]
                self.offset[0] += dx
                self.offset[1] += dy
                self.last_mouse = ev.pos
        return True

    def draw(self, snapshot: dict):
        self.screen.fill((18, 18, 22))
        nodes = {n["id"]: n for n in snapshot.get("nodes", [])}
        # edges
        for e in snapshot.get("edges", []):
            a = nodes.get(e["a"]); b = nodes.get(e["b"])
            if not a or not b: continue
            ax, ay = self.world_to_screen(a["x"], a["y"])
            bx, by = self.world_to_screen(b["x"], b["y"])
            pygame.draw.line(self.screen, COLORS["edge"], (ax, ay), (bx, by), 1)

        # nodes
        for nid, n in nodes.items():
            x, y = self.world_to_screen(n["x"], n["y"])
            col = COLORS.get(n["type"], (120,120,120))
            pygame.draw.circle(self.screen, col, (int(x), int(y)), int(6 * self.zoom + 2))
            if self.zoom > 0.6:
                label = self.font.render(str(nid), True, (200,200,200))
                self.screen.blit(label, (x+5, y-8))

        # entities grouped by node
        ent_by_node = {}
        for ent in snapshot.get("entities", []):
            ent_by_node.setdefault(ent["node_id"], []).append(ent)

        for node_id, ents in ent_by_node.items():
            n = nodes.get(node_id)
            if not n: continue
            x, y = self.world_to_screen(n["x"], n["y"])
            # stack indicator
            total = len(ents)
            for i, ent in enumerate(ents[:4]):  # show max 4
                owner = ent["owner_id"] % len(COLORS["faction"])
                fcol = COLORS["faction"][owner]
                pygame.draw.rect(self.screen, fcol, (x+8+i*7, y-12, 6, 10))
            if total > 4:
                txt = self.font.render(f"+{total-4}", True, (255,255,255))
                self.screen.blit(txt, (x+8+28, y-12))

        pygame.display.flip()
        self.clock.tick(60)

    def quit(self):
        pygame.quit()
