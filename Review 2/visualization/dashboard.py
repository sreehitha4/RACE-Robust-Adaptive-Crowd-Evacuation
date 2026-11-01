"""Interactive Dashboard with Live Egress Curve Graph, Preset Scenarios, and Inspector Dossier.

Provides telemetry, real-time S-curve graph, interactive tools,
and panic level modulation.
"""

from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple
import pygame
from evaluation.metrics import EvacuationSummary
from simulation.engine import SimulationState, CrowdMode
from agents.agent import Agent, PanicLevel
from visualization.graph import EvacuationGraph


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
        pygame.draw.rect(surface, (80, 100, 120), self.rect, width=1, border_radius=5)

        label = font.render(self.text, True, txt_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


class Dashboard:
    """Telemetry, Live Graph, Inspector HUD, and Scenario Switcher."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.buttons: List[Button] = []
        self.active_tool: MouseTool = MouseTool.INSPECT

        # Live Real-time Egress Chart
        chart_w = width - 28
        chart_h = 75
        self.graph: EvacuationGraph = EvacuationGraph((x + 14, y + 160, chart_w, chart_h))

        self.font_title: Optional[pygame.font.Font] = None
        self.font_body: Optional[pygame.font.Font] = None
        self.font_bold: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_title is None:
            self.font_title = pygame.font.SysFont("Segoe UI", 13, bold=True)
            self.font_body = pygame.font.SysFont("Segoe UI", 9)
            self.font_bold = pygame.font.SysFont("Segoe UI", 9, bold=True)
            self.font_btn = pygame.font.SysFont("Segoe UI", 9, bold=True)

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
        is_heatmap_active: bool,
        plan_name: str = "Campus Complex",
        congestion_balancing_on: bool = True,
        rerouted_count: int = 0,
        portal_queues: Optional[Dict[int, int]] = None
    ) -> None:
        self._init_fonts()

        # Panel Background
        pygame.draw.rect(surface, (24, 30, 42), self.rect)
        pygame.draw.line(surface, (45, 55, 72), (self.rect.left, self.rect.top), (self.rect.left, self.rect.bottom), 2)

        pad_x = self.rect.left + 14
        cur_y = self.rect.top + 8

        # Title
        title_surf = self.font_title.render("SIMULATION CONTROL CENTER", True, (240, 245, 250))
        surface.blit(title_surf, (pad_x, cur_y))
        cur_y += 18

        # Mode Badge
        if crowd_mode == CrowdMode.NORMAL_FLOW:
            mode_color = (46, 204, 113)
            mode_text = "MODE: NORMAL CROWD CIRCULATION"
        else:
            mode_color = (231, 76, 60)
            mode_text = "MODE: EMERGENCY EVACUATION"

        mode_rect = pygame.Rect(pad_x, cur_y, self.rect.width - 28, 18)
        pygame.draw.rect(surface, (16, 20, 28), mode_rect, border_radius=4)
        pygame.draw.rect(surface, mode_color, mode_rect, width=1, border_radius=4)
        m_lbl = self.font_bold.render(mode_text, True, mode_color)
        surface.blit(m_lbl, m_lbl.get_rect(center=mode_rect.center))
        cur_y += 22

        # State & Tool status line
        status_line = f"STATE: {state.value} | TOOL: {self.active_tool.value} ({sim_speed:.1f}x)"
        surface.blit(self.font_bold.render(status_line, True, (150, 175, 200)), (pad_x, cur_y))
        cur_y += 14

        # Occupant Dossier Card (if an agent is clicked)
        cur_y = self._render_occupant_dossier(surface, pad_x, cur_y, selected_agent)

        # Update and render the Real-Time Evacuation Curve Chart
        self.graph.rect.top = cur_y
        self.graph.record_datapoint(summary.total_ticks, summary.evacuated_agents)
        self.graph.draw(surface, total_agents=summary.total_agents)
        cur_y = self.graph.rect.bottom + 6

        # Tabulated Metrics
        cur_y = self._render_metrics_grid(
            surface, pad_x, cur_y, summary, crowd_mode, plan_name,
            congestion_balancing_on, rerouted_count, portal_queues
        )

        # Buttons
        for btn in self.buttons:
            btn.draw(surface, self.font_btn)

    def _render_occupant_dossier(
        self, surface: pygame.Surface, x: int, y: int, agent: Optional[Agent]
    ) -> int:
        card_w = self.rect.width - 28
        card_h = 60
        card_rect = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(surface, (18, 22, 32), card_rect, border_radius=5)
        pygame.draw.rect(surface, (241, 196, 15) if agent else (35, 45, 60), card_rect, width=1, border_radius=5)

        if agent is None:
            txt1 = self.font_bold.render("Occupant Inspector (Left-click any person)", True, (110, 130, 155))
            txt2 = self.font_body.render("Click a person to highlight their BFS path & stats", True, (80, 95, 115))
            surface.blit(txt1, (x + 8, y + 12))
            surface.blit(txt2, (x + 8, y + 28))
            return card_rect.bottom + 6

        name_str = f"{agent.name} (#{agent.agent_id}) — {agent.vel.length():.2f} m/s ({agent.panic_level.value})"
        group_str = f"Companion: #{agent.companion_id}" if agent.companion_id else "Solo Pedestrian"
        if getattr(agent, "rerouted", False):
            group_str += " | [REROUTED AROUND QUEUE]"

        surface.blit(self.font_bold.render(name_str, True, (241, 196, 15)), (x + 8, y + 5))
        surface.blit(self.font_body.render(group_str, True, (170, 185, 200)), (x + 8, y + 20))

        # Stress meter
        stress_pct = int(agent.stress_level * 100)
        s_bar_track = pygame.Rect(x + 8, y + 38, card_w - 16, 7)
        pygame.draw.rect(surface, (35, 45, 60), s_bar_track, border_radius=3)
        s_fill_w = int(s_bar_track.width * agent.stress_level)
        s_color = (46, 204, 113) if stress_pct < 40 else ((241, 196, 15) if stress_pct < 70 else (231, 76, 60))
        if s_fill_w > 0:
            pygame.draw.rect(surface, s_color, (s_bar_track.left, s_bar_track.top, s_fill_w, 7), border_radius=3)

        return card_rect.bottom + 6

    def _render_metrics_grid(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        summary: EvacuationSummary,
        crowd_mode: CrowdMode,
        plan_name: str,
        congestion_balancing_on: bool,
        rerouted_count: int,
        portal_queues: Optional[Dict[int, int]] = None
    ) -> int:
        card_w = self.rect.width - 28
        short_plan = plan_name.split(" ")[0] + " " + (plan_name.split(" ")[1] if len(plan_name.split(" ")) > 1 else "")
        reroute_val = f"ACTIVE ({rerouted_count} diverted)" if congestion_balancing_on else "OFF (Fixed Paths)"
        reroute_col = (46, 204, 113) if congestion_balancing_on else (145, 160, 175)

        if portal_queues:
            q_parts = [f"E{idx+1}:{cnt}" for idx, cnt in sorted(portal_queues.items())[:4]]
            q_summary = "  ".join(q_parts)
            has_jam = any(v >= 2 for v in portal_queues.values())
            q_color = (231, 76, 60) if has_jam else (46, 204, 113)
        else:
            q_summary = "All Clear"
            q_color = (46, 204, 113)

        if crowd_mode == CrowdMode.NORMAL_FLOW:
            metrics_data = [
                ("Floor Plan", f"{short_plan}", (241, 196, 15)),
                ("Exit Balancing", reroute_val, reroute_col),
                ("Portal Queues", q_summary, q_color),
                ("Circulating Crowd", f"{summary.active_agents}/{summary.total_agents}", (46, 204, 113)),
                ("Simulation Ticks", f"{summary.total_ticks}", (241, 196, 15)),
            ]
        else:
            metrics_data = [
                ("Floor Plan", f"{short_plan}", (241, 196, 15)),
                ("Exit Balancing", reroute_val, reroute_col),
                ("Portal Queues", q_summary, q_color),
                ("Evacuated Safe", f"{summary.evacuated_agents} ({summary.evacuation_percentage:.1f}%)", (46, 204, 113)),
                ("Active In Building", f"{summary.active_agents}", (52, 152, 219)),
                ("Avg Egress Time", f"{summary.avg_evacuation_ticks:.1f} ticks", (155, 89, 182)),
            ]

        card_rect = pygame.Rect(x, y, card_w, len(metrics_data) * 16 + 6)
        pygame.draw.rect(surface, (18, 22, 32), card_rect, border_radius=5)

        line_y = y + 4
        for label, val, color in metrics_data:
            lbl_surf = self.font_body.render(label, True, (145, 160, 175))
            val_surf = self.font_bold.render(val, True, color)
            surface.blit(lbl_surf, (x + 8, line_y))
            surface.blit(val_surf, (x + card_w - val_surf.get_width() - 8, line_y))
            line_y += 16

        return card_rect.bottom + 6
