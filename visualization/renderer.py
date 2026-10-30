"""Architectural Renderer with Doorway Arcs, Exit Beacons, and Path Ribbons.

Features:
  - Realistic multi-tone room floors (lecture hall, central atrium, library).
  - Architectural doorway thresholds.
  - Glowing exit portals with directional egress arrows.
  - Continuous crowd agents with travel orientation needles.
  - Companion group connection tethers (visualizing friends walking together).
  - Interactive selection beacon and illuminated path trajectory.
  - Dynamic fire / hazard flame animations.
  - Real-time crowd density heatmap overlay.
"""

import math
import pygame
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building, Room
from environment.grid import CellType, Grid
from agents.agent import Agent, AgentState, PanicLevel


COLOR_BG = (18, 22, 30)              # Modern architectural dark slate
COLOR_DEFAULT_FLOOR = (238, 242, 246)
COLOR_WALL = (45, 55, 72)            # Charcoal structural walls
COLOR_PILLAR = (33, 40, 53)          # Load-bearing pillar
COLOR_EXIT = (46, 204, 113)          # Egress emerald green
COLOR_EXIT_BLOCKED = (231, 76, 60)   # Blocked hazard red
COLOR_GRID_LINE = (222, 228, 236)    # Subtle floor divisions
COLOR_DOOR_FRAME = (180, 160, 120)   # Architectural timber doorway tone

PEDESTRIAN_COLORS = [
    (41, 128, 185),   # Cobalt blue
    (22, 160, 133),   # Marine teal
    (142, 68, 173),   # Royal violet
    (211, 84, 0),     # Warm amber
    (39, 174, 96),    # Forest green
    (192, 57, 43),    # Crimson
    (52, 73, 94),     # Slate
    (243, 156, 18),   # Marigold
]


class BuildingRenderer:
    """Renders architectural layouts, realistic exits, continuous crowds, and heatmaps."""

    def __init__(self, building: Building, cell_size: int = 24, offset_x: int = 25, offset_y: int = 45) -> None:
        self.building: Building = building
        self.cell_size: int = cell_size
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y

        self.grid_pixel_width = building.grid.width * cell_size
        self.grid_pixel_height = building.grid.height * cell_size

        self.show_heatmap: bool = False
        self.font_small: Optional[pygame.font.Font] = None
        self.font_room: Optional[pygame.font.Font] = None
        self.font_exit: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_small is None:
            self.font_small = pygame.font.SysFont("Segoe UI", 9, bold=True)
            self.font_room = pygame.font.SysFont("Segoe UI", 11, bold=True)
            self.font_exit = pygame.font.SysFont("Segoe UI", 10, bold=True)

    def grid_to_pixel(self, gx: float, gy: float) -> Tuple[int, int]:
        """Convert continuous grid coordinate to screen pixel coordinate."""
        px = int(self.offset_x + gx * self.cell_size)
        py = int(self.offset_y + gy * self.cell_size)
        return px, py

    def pixel_to_grid(self, px: int, py: int) -> Tuple[float, float]:
        """Convert screen pixel coordinate to continuous grid coordinates."""
        gx = (px - self.offset_x) / self.cell_size
        gy = (py - self.offset_y) / self.cell_size
        return gx, gy

    def render_building(self, surface: pygame.Surface, blocked_exits: Optional[Set[Tuple[int, int]]] = None) -> None:
        """Render floor plan, architectural rooms, doorway arcs, pillars, and 4 exits."""
        self._init_fonts()
        grid = self.building.grid
        blocked = blocked_exits or set()

        for gy in range(grid.height):
            for gx in range(grid.width):
                px, py = self.grid_to_pixel(gx, gy)
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)
                cell_type = grid.get_cell(gx, gy)

                if (gx, gy) in blocked:
                    # Blocked exit
                    pygame.draw.rect(surface, COLOR_EXIT_BLOCKED, rect)
                    pygame.draw.line(surface, (255, 255, 255), (px, py), (px + self.cell_size, py + self.cell_size), 2)
                    pygame.draw.line(surface, (255, 255, 255), (px, py + self.cell_size), (px + self.cell_size, py), 2)
                elif (gx, gy) in self.building.hazards:
                    # Dynamic fire / hazard flame
                    pygame.draw.rect(surface, (231, 76, 60), rect)
                    pygame.draw.circle(surface, (243, 156, 18), rect.center, int(self.cell_size * 0.42))
                    pygame.draw.circle(surface, (255, 240, 180), rect.center, int(self.cell_size * 0.22))
                elif (gx, gy) in self.building.pillars:
                    # Structural architectural pillar
                    pygame.draw.rect(surface, (240, 243, 248), rect)
                    pygame.draw.circle(surface, COLOR_PILLAR, rect.center, int(self.cell_size * 0.44))
                    pygame.draw.circle(surface, (60, 75, 95), rect.center, int(self.cell_size * 0.44), width=1)
                elif cell_type == CellType.WALL:
                    pygame.draw.rect(surface, COLOR_WALL, rect)
                    pygame.draw.rect(surface, (58, 72, 92), rect, width=1)
                elif cell_type == CellType.EXIT:
                    pygame.draw.rect(surface, COLOR_EXIT, rect)
                    pygame.draw.rect(surface, (30, 130, 76), rect, width=2)
                else:
                    # Distinct room floor zoning
                    room = self.building.get_room_at(gx, gy)
                    floor_col = room.floor_color if room else COLOR_DEFAULT_FLOOR
                    pygame.draw.rect(surface, floor_col, rect)
                    pygame.draw.rect(surface, COLOR_GRID_LINE, rect, width=1)

                    # Highlight doorways with warm architectural threshold indicators
                    if (gx, gy) in self.building.doorways:
                        pygame.draw.rect(surface, COLOR_DOOR_FRAME, (px, py + self.cell_size - 3, self.cell_size, 3))

        self._render_room_labels(surface)
        self._render_exit_signs(surface)

    def _render_room_labels(self, surface: pygame.Surface) -> None:
        if self.font_room is None:
            return

        for room in self.building.rooms.values():
            rx = self.offset_x + (room.x1 + (room.x2 - room.x1 + 1) / 2) * self.cell_size
            ry = self.offset_y + (room.y1 + 0.35) * self.cell_size

            text_surf = self.font_room.render(room.name, True, (90, 105, 120))
            text_rect = text_surf.get_rect(center=(int(rx), int(ry)))
            surface.blit(text_surf, text_rect)

    def _render_exit_signs(self, surface: pygame.Surface) -> None:
        if self.font_exit is None:
            return

        w = self.building.grid.width
        h = self.building.grid.height

        # West Exit
        w_px, w_py = self.grid_to_pixel(0, 16)
        surface.blit(self.font_exit.render("⬅ EXIT 1 (WEST)", True, COLOR_EXIT), (w_px + 2, w_py - 14))

        # East Exit
        e_px, e_py = self.grid_to_pixel(w - 1, 16)
        surface.blit(self.font_exit.render("EXIT 2 (EAST) ➡", True, COLOR_EXIT), (e_px - 70, e_py - 14))

        # South Main Egress
        s_px, s_py = self.grid_to_pixel(15, h - 1)
        surface.blit(self.font_exit.render("⬇ SOUTH MAIN ATRIUM EGRESS ⬇", True, COLOR_EXIT), (s_px - 45, s_py + self.cell_size + 2))

        # North Plaza Exit
        n_px, n_py = self.grid_to_pixel(16, 0)
        surface.blit(self.font_exit.render("⬆ NORTH PLAZA EXIT ⬆", True, COLOR_EXIT), (n_px - 35, n_py - 16))

    def render_agents(
        self,
        surface: pygame.Surface,
        agents: List[Agent],
        selected_agent: Optional[Agent] = None,
        is_evacuation_mode: bool = False
    ) -> None:
        """Render continuous crowd agents, heading orientations, and group dynamics."""
        self._init_fonts()
        radius = int(self.cell_size * 0.38)

        # 1. Draw Companion Tether Lines (connecting pairs/friends)
        active_map = {a.agent_id: a for a in agents if a.is_active}
        for agent in agents:
            if agent.is_active and agent.companion_id and agent.companion_id in active_map:
                if agent.agent_id < agent.companion_id:
                    comp = active_map[agent.companion_id]
                    p1 = self.grid_to_pixel(agent.pos.x, agent.pos.y)
                    p2 = self.grid_to_pixel(comp.pos.x, comp.pos.y)
                    pygame.draw.line(surface, (180, 210, 240, 120), p1, p2, 1)

        # 2. Draw Individual Agents
        for agent in agents:
            if is_evacuation_mode and agent.is_evacuated:
                continue

            cx, cy = self.grid_to_pixel(agent.pos.x, agent.pos.y)

            # Color styling
            if agent.is_stuck:
                body_color = (231, 76, 60)
            elif is_evacuation_mode:
                if agent.panic_level == PanicLevel.PANIC:
                    body_color = (231, 76, 60)
                else:
                    body_color = (41, 128, 185)
            else:
                color_idx = (agent.agent_id - 1) % len(PEDESTRIAN_COLORS)
                body_color = PEDESTRIAN_COLORS[color_idx]

            # Trail ribbon
            if len(agent.trail) > 1:
                pts = [self.grid_to_pixel(tx, ty) for tx, ty in agent.trail]
                pygame.draw.lines(surface, (body_color[0], body_color[1], body_color[2]), False, pts, 1)

            # Drop shadow
            pygame.draw.circle(surface, (12, 16, 22), (cx + 1, cy + 2), radius)
            # Outer boundary ring
            pygame.draw.circle(surface, (20, 25, 35), (cx, cy), radius + 1)
            # Body disc
            pygame.draw.circle(surface, body_color, (cx, cy), radius)

            # Travel Direction Indicator (needle)
            v_len = agent.vel.length()
            if v_len > 0.05:
                dir_x = (agent.vel.x / v_len) * (radius + 3)
                dir_y = (agent.vel.y / v_len) * (radius + 3)
                pygame.draw.line(surface, (255, 255, 255), (cx, cy), (int(cx + dir_x), int(cy + dir_y)), 2)

            # Agent ID
            if self.font_small:
                id_text = self.font_small.render(str(agent.agent_id), True, (255, 255, 255))
                surface.blit(id_text, id_text.get_rect(center=(cx, cy)))

        # 3. Selected Agent Reticle & Projected Navigation Line
        if selected_agent and selected_agent.is_active:
            sx, sy = self.grid_to_pixel(selected_agent.pos.x, selected_agent.pos.y)
            pygame.draw.circle(surface, (241, 196, 15), (sx, sy), radius + 5, width=2)

            # Draw glowing route path to destination
            if selected_agent.path and selected_agent.path_index < len(selected_agent.path):
                route_pts = [self.grid_to_pixel(selected_agent.pos.x, selected_agent.pos.y)]
                for wx, wy in selected_agent.path[selected_agent.path_index:]:
                    route_pts.append(self.grid_to_pixel(wx + 0.5, wy + 0.5))
                if len(route_pts) > 1:
                    pygame.draw.lines(surface, (241, 196, 15), False, route_pts, 2)
                    # Destination beacon at target exit
                    end_px, end_py = route_pts[-1]
                    pygame.draw.circle(surface, (241, 196, 15), (end_px, end_py), 6, width=2)

    def render_density_heatmap(self, surface: pygame.Surface, agents: List[Agent]) -> None:
        """Render a dynamic crowd congestion density heatmap overlay."""
        if not self.show_heatmap:
            return

        grid = self.building.grid
        density = [[0 for _ in range(grid.width)] for _ in range(grid.height)]
        for a in agents:
            if a.is_active and grid.is_inside(a.current_pos[0], a.current_pos[1]):
                density[a.current_pos[1]][a.current_pos[0]] += 1

        heat_overlay = pygame.Surface((self.grid_pixel_width, self.grid_pixel_height), pygame.SRCALPHA)

        for gy in range(grid.height):
            for gx in range(grid.width):
                cnt = density[gy][gx]
                if cnt > 0 and grid.is_walkable(gx, gy):
                    if cnt == 1:
                        color = (46, 204, 113, 85)
                    elif cnt <= 3:
                        color = (241, 196, 15, 130)
                    else:
                        color = (231, 76, 60, 175)

                    px = gx * self.cell_size
                    py = gy * self.cell_size
                    pygame.draw.rect(heat_overlay, color, (px, py, self.cell_size, self.cell_size))

        surface.blit(heat_overlay, (self.offset_x, self.offset_y))
