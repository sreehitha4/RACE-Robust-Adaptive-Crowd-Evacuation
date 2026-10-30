"""Pygame Renderer for the Building Grid and Crowd Agents.

Features:
  - 4 prominent, distinct exits (South Main Egress, North Plaza, West Wing, East Wing).
  - Smooth 60 FPS sub-pixel continuous interpolation for fluid human walking.
  - Multi-hue pedestrian styling in Normal Flow and alert highlights in Evacuation.
  - Architectural zoning with room titles and exit banners.
"""

import math
import pygame
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building, Room
from environment.grid import CellType, Grid
from agents.agent import Agent, AgentState


# Architectural Palette
COLOR_BG = (22, 27, 34)             # Modern dark slate background
COLOR_FLOOR = (238, 242, 246)       # Architectural light floor
COLOR_WALL = (45, 55, 72)           # Solid dark wall
COLOR_EXIT = (46, 204, 113)         # Emerald exit portal
COLOR_EXIT_BLOCKED = (231, 76, 60)  # Hazard blocked exit
COLOR_GRID_LINE = (218, 224, 233)   # Subtle floor divisions

# Normal Crowd pedestrian diverse hues
PEDESTRIAN_COLORS = [
    (41, 128, 185),   # Cobalt blue
    (22, 160, 133),   # Marine teal
    (142, 68, 173),   # Royal violet
    (211, 84, 0),     # Warm amber
    (39, 174, 96),    # Forest green
    (192, 57, 43),    # Crimson
]

COLOR_AGENT_OUTLINE = (20, 25, 35)


class BuildingRenderer:
    """Renders architectural layouts, realistic exits, and fluid crowd animations."""

    def __init__(self, building: Building, cell_size: int = 28, offset_x: int = 20, offset_y: int = 50) -> None:
        self.building: Building = building
        self.cell_size: int = cell_size
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y

        self.grid_pixel_width = building.grid.width * cell_size
        self.grid_pixel_height = building.grid.height * cell_size

        self.font_small: Optional[pygame.font.Font] = None
        self.font_room: Optional[pygame.font.Font] = None
        self.font_exit: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_small is None:
            self.font_small = pygame.font.SysFont("Segoe UI", 10, bold=True)
            self.font_room = pygame.font.SysFont("Segoe UI", 12, bold=True)
            self.font_exit = pygame.font.SysFont("Segoe UI", 11, bold=True)

    def grid_to_pixel(self, gx: float, gy: float) -> Tuple[int, int]:
        """Convert discrete or continuous grid coordinate to screen pixel coordinate."""
        px = int(self.offset_x + gx * self.cell_size)
        py = int(self.offset_y + gy * self.cell_size)
        return px, py

    def render_building(self, surface: pygame.Surface, blocked_exits: Optional[Set[Tuple[int, int]]] = None) -> None:
        """Render floor tiles, walls, grid lines, and all 4 prominent exits."""
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
                elif cell_type == CellType.WALL:
                    pygame.draw.rect(surface, COLOR_WALL, rect)
                    pygame.draw.rect(surface, (60, 75, 95), rect, width=1)
                elif cell_type == CellType.EXIT:
                    pygame.draw.rect(surface, COLOR_EXIT, rect)
                    # Outer exit glow line
                    pygame.draw.rect(surface, (30, 130, 76), rect, width=2)
                else:
                    # Walkable floor
                    pygame.draw.rect(surface, COLOR_FLOOR, rect)
                    pygame.draw.rect(surface, COLOR_GRID_LINE, rect, width=1)

        # Draw room titles
        self._render_room_labels(surface)

        # Draw distinct exit signs for all 4 locations
        self._render_exit_signs(surface)

    def _render_room_labels(self, surface: pygame.Surface) -> None:
        """Draw room banners over interior zones."""
        if self.font_room is None:
            return

        for room in self.building.rooms.values():
            rx = self.offset_x + (room.x1 + (room.x2 - room.x1 + 1) / 2) * self.cell_size
            ry = self.offset_y + (room.y1 + 0.35) * self.cell_size

            text_surf = self.font_room.render(room.name, True, (80, 95, 110))
            text_rect = text_surf.get_rect(center=(int(rx), int(ry)))
            surface.blit(text_surf, text_rect)

    def _render_exit_signs(self, surface: pygame.Surface) -> None:
        """Render distinct text signs identifying each of the 4 building exits."""
        if self.font_exit is None:
            return

        w = self.building.grid.width
        h = self.building.grid.height

        # 1. West Wing Exit
        w_px, w_py = self.grid_to_pixel(0, 15)
        w_surf = self.font_exit.render("WEST EXIT", True, COLOR_EXIT)
        surface.blit(w_surf, (w_px, w_py - 16))

        # 2. East Wing Exit
        e_px, e_py = self.grid_to_pixel(w - 1, 15)
        e_surf = self.font_exit.render("EAST EXIT", True, COLOR_EXIT)
        surface.blit(e_surf, (e_px - 40, e_py - 16))

        # 3. South Main Entrance / Egress
        s_px, s_py = self.grid_to_pixel(13, h - 1)
        s_surf = self.font_exit.render("MAIN ATRIUM ENTRANCE / EXIT", True, COLOR_EXIT)
        surface.blit(s_surf, (s_px - 35, s_py + self.cell_size + 4))

        # 4. North Plaza Exit
        n_px, n_py = self.grid_to_pixel(14, 0)
        n_surf = self.font_exit.render("NORTH PLAZA EXIT", True, COLOR_EXIT)
        surface.blit(n_surf, (n_px - 25, n_py - 18))

    def render_agents(
        self,
        surface: pygame.Surface,
        agents: List[Agent],
        is_evacuation_mode: bool = False
    ) -> None:
        """Draw agents at their smooth interpolated visual coordinates."""
        self._init_fonts()
        radius = int(self.cell_size * 0.36)

        for agent in agents:
            # In evacuation mode, hide completely evacuated agents; in normal mode, keep all active
            if is_evacuation_mode and agent.is_evacuated:
                continue

            # Update smooth continuous position towards grid cell
            agent.update_visual(lerp_speed=0.28)

            px, py = self.grid_to_pixel(agent.visual_x, agent.visual_y)
            center_x = px + self.cell_size // 2
            center_y = py + self.cell_size // 2

            # Determine color
            if agent.is_stuck:
                body_color = (231, 76, 60)
            elif is_evacuation_mode:
                # Urgent blue/orange in evacuation
                body_color = (41, 128, 185)
            else:
                # Diverse natural pedestrian clothing colors in normal mode!
                color_idx = (agent.agent_id - 1) % len(PEDESTRIAN_COLORS)
                body_color = PEDESTRIAN_COLORS[color_idx]

            # Drop shadow
            pygame.draw.circle(surface, (15, 20, 28), (center_x + 1, center_y + 2), radius)
            # Outline
            pygame.draw.circle(surface, COLOR_AGENT_OUTLINE, (center_x, center_y), radius + 1)
            # Fill disc
            pygame.draw.circle(surface, body_color, (center_x, center_y), radius)

            # Draw Agent ID
            if self.font_small:
                id_text = self.font_small.render(str(agent.agent_id), True, (255, 255, 255))
                surface.blit(id_text, id_text.get_rect(center=(center_x, center_y)))
