"""Interactive Dashboard with Inspector Dossier, Tool Palette, and Panic Modulator.

Provides real-time telemetry, click-to-inspect occupant data,
mouse interaction tools, and mode toggles.
"""

from enum import Enum
from typing import Callable, List, Optional, Tuple
import pygame
from evaluation.metrics import EvacuationSummary
from simulation.engine import SimulationState, CrowdMode
from agents.agent import Agent, PanicLevel


class MouseTool(Enum):
    INSPECT = "INSPECT"
    PLACE_HAZARD = "PLACE_HAZARD"
    SPAWN_PERSON = "SPAWN_PERSON"


class Button:
    """Clickable UI button with hover states and active highlights."""

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        callback: Callable[[], None],
        bg_color: Tuple[int, int, int] = (52, 73, 94),
        hover_color: Tuple[int, int, int] = (74, 105, 135),
        text_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.text: str = text
        self.callback: Callable[[], None] = callback
        self.bg_color: Tuple[int, int, int] = bg_color
        self.hover_color: Tuple[int, int, int] = hover_color
        self.text_color: Tuple[int, int, int] = text_color
        self.is_hovered: bool = False
        self.is_active: bool = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.is_active:
            color = (241, 196, 15)
            txt_color = (20, 24, 32)
        else:
            color = self.hover_color if self.is_hovered else self.bg_color
            txt_color = self.text_color

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (90, 110, 130), self.rect, width=1, border_radius=5)

        label = font.render(self.text, True, txt_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


class Dashboard:
    """Telemetry, Inspector HUD, and Interactive Tool Palette."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.buttons: List[Button] = []
        self.active_tool: MouseTool = MouseTool.INSPECT

        self.font_title: Optional[pygame.font.Font] = None
        self.font_section: Optional[pygame.font.Font] = None
        self.font_body: Optional[pygame.font.Font] = None
        self.font_bold: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_title is None:
            self.font_title = pygame.font.SysFont("Segoe UI", 14, bold=True)
            self.font_section = pygame.font.SysFont("Segoe UI", 11, bold=True)
            self.font_body = pygame.font.SysFont("Segoe UI", 10)
            self.font_bold = pygame.font.SysFont("Segoe UI", 10, bold=True)
            self.font_btn = pygame.font.SysFont("Segoe UI", 10, bold=True)

    def add_button(self, button: Button) -> None:
        self.buttons.append(button)

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def render(
        self,
        surface: pygame.Surface,
        summary: EvacuationSummary,
        state: SimulationState,
        crowd_mode: CrowdMode,
        sim_speed: float,
        selected_agent: Optional[Agent],
        is_heatmap_active: bool
    ) -> None:
        self._init_fonts()

        # Panel Background
        pygame.draw.rect(surface, (26, 32, 44), self.rect)
        pygame.draw.line(surface, (45, 55, 72), (self.rect.left, self.rect.top), (self.rect.left, self.rect.bottom), 2)

        pad_x = self.rect.left + 14
        cur_y = self.rect.top + 12

        # Header Title
        title_surf = self.font_title.render("SIMULATION CONTROL CENTER", True, (240, 245, 250))
        surface.blit(title_surf, (pad_x, cur_y))
        cur_y += 22

        # Mode Badge
        if crowd_mode == CrowdMode.NORMAL_FLOW:
            mode_color = (46, 204, 113)
            mode_text = "MODE: NORMAL CROWD FLOW"
        else:
            mode_color = (231, 76, 60)
            mode_text = "MODE: EMERGENCY EVACUATION"

        mode_rect = pygame.Rect(pad_x, cur_y, self.rect.width - 28, 22)
        pygame.draw.rect(surface, (18, 22, 30), mode_rect, border_radius=4)
        pygame.draw.rect(surface, mode_color, mode_rect, width=2, border_radius=4)
        m_lbl = self.font_bold.render(mode_text, True, mode_color)
        surface.blit(m_lbl, m_lbl.get_rect(center=mode_rect.center))
        cur_y += 26

        # State & Tool status line
        tool_text = f"TOOL: {self.active_tool.value} | {state.value} ({sim_speed:.1f}x)"
        tool_lbl = self.font_bold.render(tool_text, True, (160, 180, 200))
        surface.blit(tool_lbl, (pad_x, cur_y))
        cur_y += 18

        # Occupant Dossier Card (if someone is clicked!)
        cur_y = self._render_occupant_dossier(surface, pad_x, cur_y, selected_agent)

        # Tabulated Metrics
        cur_y = self._render_metrics_grid(surface, pad_x, cur_y, summary, crowd_mode)

        # Buttons
        for btn in self.buttons:
            btn.draw(surface, self.font_btn)

    def _render_occupant_dossier(
        self, surface: pygame.Surface, x: int, y: int, agent: Optional[Agent]
    ) -> int:
        """Render live telemetry dossier of the selected person."""
        card_w = self.rect.width - 28
        card_h = 74
        card_rect = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(surface, (20, 25, 35), card_rect, border_radius=6)
        pygame.draw.rect(surface, (241, 196, 15) if agent else (40, 50, 65), card_rect, width=1, border_radius=6)

        if agent is None:
            txt1 = self.font_bold.render("Occupant Inspector (Click any person)", True, (120, 140, 160))
            txt2 = self.font_body.render("Left-click on any person to view dossier", True, (80, 100, 120))
            surface.blit(txt1, (x + 8, y + 16))
            surface.blit(txt2, (x + 8, y + 36))
            return card_rect.bottom + 10

        # Person details
        name_str = f"{agent.name} (ID #{agent.agent_id})"
        group_str = f"Walking with Companion #{agent.companion_id}" if agent.companion_id else "Solo Pedestrian"
        speed_str = f"Speed: {agent.vel.length():.2f} m/s ({agent.panic_level.value})"

        surface.blit(self.font_bold.render(name_str, True, (241, 196, 15)), (x + 8, y + 6))
        surface.blit(self.font_body.render(group_str, True, (180, 190, 200)), (x + 8, y + 24))
        surface.blit(self.font_body.render(speed_str, True, (160, 210, 240)), (x + 8, y + 40))

        # Stress meter
        stress_pct = int(agent.stress_level * 100)
        s_bar_track = pygame.Rect(x + 8, y + 58, card_w - 16, 8)
        pygame.draw.rect(surface, (40, 50, 65), s_bar_track, border_radius=3)
        s_fill_w = int(s_bar_track.width * agent.stress_level)
        s_color = (46, 204, 113) if stress_pct < 40 else ((241, 196, 15) if stress_pct < 70 else (231, 76, 60))
        if s_fill_w > 0:
            pygame.draw.rect(surface, s_color, (s_bar_track.left, s_bar_track.top, s_fill_w, 8), border_radius=3)

        return card_rect.bottom + 10

    def _render_metrics_grid(
        self, surface: pygame.Surface, x: int, y: int, summary: EvacuationSummary, crowd_mode: CrowdMode
    ) -> int:
        card_w = self.rect.width - 28
        if crowd_mode == CrowdMode.NORMAL_FLOW:
            metrics_data = [
                ("Total Population", f"{summary.total_agents}", (220, 220, 220)),
                ("Circulating Pedestrians", f"{summary.active_agents}", (46, 204, 113)),
                ("Continuous Exits", "4 Portals Active", (52, 152, 219)),
                ("Simulation Ticks", f"{summary.total_ticks}", (241, 196, 15)),
                ("Crowd Delay Ticks", f"{summary.total_wait_ticks}", (230, 126, 34)),
            ]
        else:
            metrics_data = [
                ("Total Occupants", f"{summary.total_agents}", (220, 220, 220)),
                ("Evacuated Safe", f"{summary.evacuated_agents} ({summary.evacuation_percentage:.1f}%)", (46, 204, 113)),
                ("Active In Building", f"{summary.active_agents}", (52, 152, 219)),
                ("Simulation Ticks", f"{summary.total_ticks}", (241, 196, 15)),
                ("Avg Egress Time", f"{summary.avg_evacuation_ticks:.1f} ticks", (155, 89, 182)),
            ]

        card_rect = pygame.Rect(x, y, card_w, len(metrics_data) * 20 + 8)
        pygame.draw.rect(surface, (20, 25, 35), card_rect, border_radius=6)

        line_y = y + 5
        for label, val, color in metrics_data:
            lbl_surf = self.font_body.render(label, True, (150, 165, 180))
            val_surf = self.font_bold.render(val, True, color)
            surface.blit(lbl_surf, (x + 8, line_y))
            surface.blit(val_surf, (x + card_w - val_surf.get_width() - 8, line_y))
            line_y += 20

        return card_rect.bottom + 10
