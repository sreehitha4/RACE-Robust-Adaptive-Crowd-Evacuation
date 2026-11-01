"""Real-time Evacuation Curve and Telemetry Chart for Pygame.

Plots cumulative evacuated agents over simulation time, rendering
the classic S-curve egress chart used in civil safety engineering.
"""

from typing import List, Optional, Tuple
import pygame


class EvacuationGraph:
    """Renders a real-time line chart plotting Evacuated Population vs. Time."""

    def __init__(self, rect: Tuple[int, int, int, int]) -> None:
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.history: List[Tuple[int, int]] = [(0, 0)]  # (tick, evacuated_count)
        self.font: Optional[pygame.font.Font] = None

    def _init_font(self) -> None:
        if self.font is None:
            self.font = pygame.font.SysFont("Segoe UI", 9)

    def record_datapoint(self, tick: int, evacuated_count: int) -> None:
        """Add a data point if tick progressed."""
        if not self.history or self.history[-1][0] != tick:
            self.history.append((tick, evacuated_count))

    def reset(self) -> None:
        """Clear graph data."""
        self.history = [(0, 0)]

    def draw(self, surface: pygame.Surface, total_agents: int) -> None:
        """Draw the real-time curve on the dashboard."""
        self._init_font()

        # Frame background
        pygame.draw.rect(surface, (18, 22, 30), self.rect, border_radius=5)
        pygame.draw.rect(surface, (40, 50, 65), self.rect, width=1, border_radius=5)

        # Title
        if self.font:
            t_surf = self.font.render("Live Egress Curve (Evacuated vs Time)", True, (160, 180, 200))
            surface.blit(t_surf, (self.rect.left + 6, self.rect.top + 4))

        if len(self.history) < 2 or total_agents <= 0:
            return

        max_tick = max(self.history[-1][0], 20)
        max_evac = max(total_agents, 1)

        # Plot margins inside rect
        m_left = self.rect.left + 18
        m_right = self.rect.right - 8
        m_top = self.rect.top + 20
        m_bottom = self.rect.bottom - 12

        plot_w = m_right - m_left
        plot_h = m_bottom - m_top

        # Axis lines
        pygame.draw.line(surface, (55, 68, 85), (m_left, m_bottom), (m_right, m_bottom), 1)
        pygame.draw.line(surface, (55, 68, 85), (m_left, m_top), (m_left, m_bottom), 1)

        # Map history points to pixels
        points: List[Tuple[int, int]] = []
        for tick, count in self.history:
            px = int(m_left + (tick / max_tick) * plot_w)
            py = int(m_bottom - (count / max_evac) * plot_h)
            points.append((px, py))

        if len(points) >= 2:
            pygame.draw.lines(surface, (46, 204, 113), False, points, 2)
            # Draw current head dot
            pygame.draw.circle(surface, (46, 204, 113), points[-1], 3)
