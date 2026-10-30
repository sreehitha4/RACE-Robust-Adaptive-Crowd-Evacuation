"""Interactive Dashboard and UI Control Panel for Pygame.

Renders real-time telemetry, progress meters, control buttons,
and simulation status badges in a sleek dark theme.
"""

from typing import Callable, List, Optional, Tuple
import pygame
from evaluation.metrics import EvacuationSummary
from simulation.engine import SimulationState


class Button:
    """Clickable UI button with hover states and callbacks."""

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

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process mouse movement and click events."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Render button to surface."""
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (100, 120, 140), self.rect, width=1, border_radius=6)

        label = font.render(self.text, True, self.text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


class Dashboard:
    """Telemetry and Control Dashboard rendered on the side of the simulation view."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.buttons: List[Button] = []

        self.font_title: Optional[pygame.font.Font] = None
        self.font_section: Optional[pygame.font.Font] = None
        self.font_body: Optional[pygame.font.Font] = None
        self.font_bold: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_title is None:
            self.font_title = pygame.font.SysFont("Segoe UI", 16, bold=True)
            self.font_section = pygame.font.SysFont("Segoe UI", 13, bold=True)
            self.font_body = pygame.font.SysFont("Segoe UI", 12)
            self.font_bold = pygame.font.SysFont("Segoe UI", 12, bold=True)
            self.font_btn = pygame.font.SysFont("Segoe UI", 12, bold=True)

    def add_button(self, button: Button) -> None:
        """Register a button on the dashboard."""
        self.buttons.append(button)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatch event to all buttons."""
        for btn in self.buttons:
            btn.handle_event(event)

    def render(
        self,
        surface: pygame.Surface,
        summary: EvacuationSummary,
        state: SimulationState,
        sim_speed: float,
        is_west_exit_blocked: bool
    ) -> None:
        """Render dashboard panels, metrics, progress bar, and buttons."""
        self._init_fonts()

        # Panel Background
        pygame.draw.rect(surface, (30, 36, 48), self.rect)
        pygame.draw.line(
            surface, (50, 60, 75),
            (self.rect.left, self.rect.top),
            (self.rect.left, self.rect.bottom),
            2
        )

        pad_x = self.rect.left + 16
        cur_y = self.rect.top + 16

        # Header Title
        title_surf = self.font_title.render("EVACUATION DASHBOARD", True, (240, 245, 250))
        surface.blit(title_surf, (pad_x, cur_y))
        cur_y += 28

        # Simulation State Badge
        state_colors = {
            SimulationState.RUNNING: (46, 204, 113),
            SimulationState.PAUSED: (241, 196, 15),
            SimulationState.STOPPED: (149, 165, 166),
            SimulationState.COMPLETED: (52, 152, 219),
        }
        badge_color = state_colors.get(state, (180, 180, 180))
        badge_rect = pygame.Rect(pad_x, cur_y, self.rect.width - 32, 26)
        pygame.draw.rect(surface, (20, 24, 32), badge_rect, border_radius=4)
        pygame.draw.rect(surface, badge_color, badge_rect, width=1, border_radius=4)

        status_text = f"STATUS: {state.value} | SPEED: {sim_speed:.1f}x"
        status_surf = self.font_bold.render(status_text, True, badge_color)
        surface.blit(status_surf, status_surf.get_rect(center=badge_rect.center))
        cur_y += 36

        # Progress Bar Card
        bar_card = pygame.Rect(pad_x, cur_y, self.rect.width - 32, 54)
        pygame.draw.rect(surface, (22, 26, 35), bar_card, border_radius=6)

        pct_label = self.font_bold.render(
            f"Evacuation Progress: {summary.evacuation_percentage:.1f}%", True, (230, 235, 240)
        )
        surface.blit(pct_label, (bar_card.left + 10, bar_card.top + 8))

        # Progress Bar Track & Fill
        bar_track = pygame.Rect(bar_card.left + 10, bar_card.top + 28, bar_card.width - 20, 14)
        pygame.draw.rect(surface, (45, 52, 65), bar_track, border_radius=4)

        fill_width = int(bar_track.width * (summary.evacuation_percentage / 100.0))
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_track.left, bar_track.top, fill_width, bar_track.height)
            pygame.draw.rect(surface, (46, 204, 113), fill_rect, border_radius=4)

        cur_y += 66

        # Metrics Card Grid
        cur_y = self._render_metrics_grid(surface, pad_x, cur_y, summary)

        # Control Buttons
        for btn in self.buttons:
            btn.draw(surface, self.font_btn)

    def _render_metrics_grid(
        self, surface: pygame.Surface, x: int, y: int, summary: EvacuationSummary
    ) -> int:
        """Render tabulated metrics breakdown."""
        metrics_data = [
            ("Total Population", f"{summary.total_agents}", (220, 220, 220)),
            ("Active Agents", f"{summary.active_agents}", (52, 152, 219)),
            ("Evacuated Agents", f"{summary.evacuated_agents}", (46, 204, 113)),
            ("Stuck / Blocked", f"{summary.stuck_agents}", (231, 76, 60)),
            ("Simulation Ticks", f"{summary.total_ticks}", (241, 196, 15)),
            ("Avg Evac Time", f"{summary.avg_evacuation_ticks:.1f} ticks", (155, 89, 182)),
            ("Congestion Delays", f"{summary.total_wait_ticks} wait-ticks", (230, 126, 34)),
        ]

        card_rect = pygame.Rect(x, y, self.rect.width - 32, len(metrics_data) * 24 + 14)
        pygame.draw.rect(surface, (22, 26, 35), card_rect, border_radius=6)

        line_y = y + 8
        for label, val, color in metrics_data:
            lbl_surf = self.font_body.render(label, True, (160, 170, 180))
            val_surf = self.font_bold.render(val, True, color)

            surface.blit(lbl_surf, (x + 10, line_y))
            surface.blit(val_surf, (x + card_rect.width - val_surf.get_width() - 10, line_y))
            line_y += 24

        return card_rect.bottom + 16
