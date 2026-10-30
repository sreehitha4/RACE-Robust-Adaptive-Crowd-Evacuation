"""Pygame Renderer for the 2D Building Grid and Crowd Agents.

Renders high-contrast architectural floor plans, room zoning,
animated agents, and emergency exits with crisp visual styling.
"""

import pygame
from typing import Dict, List, Optional, Tuple
from environment.building import Building, Room
from environment.grid import CellType, Grid
from agents.agent import Agent, AgentState


# Palette definitions
COLOR_BG = (24, 28, 36)            # Dark aesthetic background
COLOR_FLOOR = (236, 240, 241)       # Clean off-white walkable floor
COLOR_WALL = (44, 62, 80)           # Dark slate architectural wall
COLOR_EXIT = (46, 204, 113)         # Vibrant emerald green exit
COLOR_EXIT_BLOCKED = (231, 76, 60)  # Hazard crimson for blocked exit
COLOR_GRID_LINE = (210, 215, 220)   # Subtle floor grid divisions

# Agent styling
COLOR_AGENT_ACTIVE = (41, 128, 185)    # Vibrant cobalt blue
COLOR_AGENT_OUTLINE = (25, 42, 86)     # Deep navy outline
COLOR_AGENT_STUCK = (192, 57, 43)      # Alert crimson
COLOR_AGENT_EVACUATED = (39, 174, 96)  # Triumph green

# Room label styling
COLOR_LABEL_BG = (52, 73, 94, 180)
COLOR_TEXT_WHITE = (245, 245, 245)
COLOR_TEXT_MUTED = (127, 140, 141)


class BuildingRenderer:
    """Renders the building grid, rooms, corridors, and crowd agents."""

    def __init__(self, building: Building, cell_size: int = 28, offset_x: int = 20, offset_y: int = 50) -> None:
        self.building: Building = building
        self.cell_size: int = cell_size
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y

        self.grid_pixel_width = building.grid.width * cell_size
        self.grid_pixel_height = building.grid.height * cell_size

        # Fonts (initialized lazily or upon render)
        self.font_small: Optional[pygame.font.Font] = None
        self.font_room: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_small is None:
            self.font_small = pygame.font.SysFont("Segoe UI", 11, bold=True)
            self.font_room = pygame.font.SysFont("Segoe UI", 12, bold=True)

    def grid_to_pixel(self, gx: int, gy: int) -> Tuple[int, int]:
        """Convert discrete grid coordinate to screen pixel coordinate."""
        px = self.offset_x + gx * self.cell_size
        py = self.offset_y + gy * self.cell_size
        return px, py

    def render_building(self, surface: pygame.Surface, blocked_exits: Optional[set] = None) -> None:
        """Render floor tiles, walls, grid lines, and exits."""
        self._init_fonts()
        grid = self.building.grid
        blocked = blocked_exits or set()

        for gy in range(grid.height):
            for gx in range(grid.width):
                px, py = self.grid_to_pixel(gx, gy)
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)
                cell_type = grid.get_cell(gx, gy)

                if (gx, gy) in blocked:
                    # Dynamically blocked exit
                    pygame.draw.rect(surface, COLOR_EXIT_BLOCKED, rect)
                    # Cross hatch
                    pygame.draw.line(surface, (255, 255, 255), (px, py), (px + self.cell_size, py + self.cell_size), 2)
                    pygame.draw.line(surface, (255, 255, 255), (px, py + self.cell_size), (px + self.cell_size, py), 2)
                elif cell_type == CellType.WALL:
                    pygame.draw.rect(surface, COLOR_WALL, rect)
                    # Subtle bevel highlight
                    pygame.draw.rect(surface, (58, 80, 102), rect, width=1)
                elif cell_type == CellType.EXIT:
                    pygame.draw.rect(surface, COLOR_EXIT, rect)
                    # Exit border glow
                    pygame.draw.rect(surface, (30, 130, 76), rect, width=2)
                else:
                    # Walkable floor
                    pygame.draw.rect(surface, COLOR_FLOOR, rect)
                    pygame.draw.rect(surface, COLOR_GRID_LINE, rect, width=1)

        # Render architectural room labels
        self._render_room_labels(surface)

    def _render_room_labels(self, surface: pygame.Surface) -> None:
        """Draw unobtrusive room title banners over interior zones."""
        if self.font_room is None:
            return

        for room in self.building.rooms.values():
            # Compute top-center pixel position of room
            rx = self.offset_x + (room.x1 + (room.x2 - room.x1 + 1) / 2) * self.cell_size
            ry = self.offset_y + (room.y1 + 0.3) * self.cell_size

            text_surf = self.font_room.render(room.name, True, (90, 100, 110))
            text_rect = text_surf.get_rect(center=(int(rx), int(ry)))
            surface.blit(text_surf, text_rect)

        # Draw EXIT text signs next to exits
        if self.font_small:
            # West Exit sign
            w_px, w_py = self.grid_to_pixel(0, 15)
            w_text = self.font_small.render("EXIT 1", True, COLOR_EXIT)
            surface.blit(w_text, (w_px, w_py - 14))

            # East Exit sign
            e_px, e_py = self.grid_to_pixel(self.building.grid.width - 1, 15)
            e_text = self.font_small.render("EXIT 2", True, COLOR_EXIT)
            surface.blit(e_text, (e_px - 8, e_py - 14))

    def render_agents(self, surface: pygame.Surface, agents: List[Agent]) -> None:
        """Draw active and stuck agents as crisp anti-aliased circles."""
        self._init_fonts()
        radius = int(self.cell_size * 0.38)

        for agent in agents:
            if agent.is_evacuated:
                continue  # Evacuated agents have exited the floor plan

            gx, gy = agent.current_pos
            px, py = self.grid_to_pixel(gx, gy)
            center_x = px + self.cell_size // 2
            center_y = py + self.cell_size // 2

            # Pick color by state
            if agent.is_stuck:
                body_color = COLOR_AGENT_STUCK
            else:
                body_color = COLOR_AGENT_ACTIVE

            # Draw outer shadow / ring
            pygame.draw.circle(surface, COLOR_AGENT_OUTLINE, (center_x, center_y), radius + 1)
            # Draw agent disc
            pygame.draw.circle(surface, body_color, (center_x, center_y), radius)

            # Draw Agent ID number inside disc
            if self.font_small:
                id_text = self.font_small.render(str(agent.agent_id), True, (255, 255, 255))
                id_rect = id_text.get_rect(center=(center_x, center_y))
                surface.blit(id_text, id_rect)
