"""Main entry point for the Crowd Evacuation & Normal Pedestrian Simulation.

Features:
  - Dual Mode: Normal Everyday Crowd Flow vs. Emergency Evacuation.
  - 4 Distinct Building Exits (North, South Main Egress, West, East).
  - Smooth 60 FPS sub-pixel continuous walking animation.
  - Interactive Mode Toggle, Speed Control, and Dynamic Rerouting.
"""

import sys
import pygame
from environment.building import Building
from simulation.engine import SimulationEngine, SimulationState, CrowdMode
from visualization.renderer import BuildingRenderer
from visualization.dashboard import Dashboard, Button


def create_simulation_app() -> None:
    """Initialize and run the crowd simulation application."""
    pygame.init()
    pygame.font.init()

    # Geometry setup
    grid_cols = 30
    grid_rows = 20
    cell_size = 28
    margin_left = 30
    margin_top = 50

    grid_px_w = grid_cols * cell_size
    grid_px_h = grid_rows * cell_size

    dash_x = margin_left + grid_px_w + 30
    dash_w = 340
    window_w = dash_x + dash_w + 24
    window_h = max(grid_px_h + margin_top + 60, 680)

    # Initialize Pygame Display
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("2D Crowd Simulation — Normal Pedestrian Dynamics & Evacuation")
    clock = pygame.time.Clock()

    # Domain instances
    building = Building.create_default(width=grid_cols, height=grid_rows)
    # Starts in Normal Crowd Flow mode by default!
    engine = SimulationEngine(building=building, agent_count=20, seed=42)
    renderer = BuildingRenderer(
        building=building,
        cell_size=cell_size,
        offset_x=margin_left,
        offset_y=margin_top
    )

    # Dashboard instance
    dashboard = Dashboard(
        x=dash_x,
        y=margin_top - 20,
        width=dash_w,
        height=window_h - margin_top
    )

    # Simulation speed parameters
    speed_levels = [1.0, 2.0, 4.0, 0.5]
    speed_idx = 0
    base_tick_delay_ms = 220.0

    # Button Callbacks
    def on_start() -> None:
        engine.start()

    def on_pause() -> None:
        engine.pause()

    def on_resume() -> None:
        engine.resume()

    def on_reset() -> None:
        engine.reset()

    def on_new_seed() -> None:
        engine.restart_with_new_seed()

    def on_cycle_speed() -> None:
        nonlocal speed_idx
        speed_idx = (speed_idx + 1) % len(speed_levels)
        speed_btn.text = f"Speed: {speed_levels[speed_idx]:.1f}x"

    def on_toggle_mode() -> None:
        """Toggle between Normal Crowd Flow and Emergency Evacuation."""
        if engine.crowd_mode == CrowdMode.NORMAL_FLOW:
            engine.set_mode(CrowdMode.EVACUATION)
            mode_toggle_btn.text = "🏢 Switch to Normal Flow"
            mode_toggle_btn.bg_color = (39, 174, 96)
            mode_toggle_btn.hover_color = (46, 204, 113)
        else:
            engine.set_mode(CrowdMode.NORMAL_FLOW)
            mode_toggle_btn.text = "🚨 Trigger Evacuation"
            mode_toggle_btn.bg_color = (192, 57, 43)
            mode_toggle_btn.hover_color = (231, 76, 60)

    def on_toggle_west_exit() -> None:
        # West exit cells: (0, 15) and (0, 16)
        engine.toggle_exit_block((0, 15))
        is_blocked = engine.toggle_exit_block((0, 16))
        if is_blocked:
            block_btn.text = "Unblock West Exit"
            block_btn.bg_color = (192, 57, 43)
            block_btn.hover_color = (231, 76, 60)
        else:
            block_btn.text = "Block West Exit (Test Rerouting)"
            block_btn.bg_color = (211, 84, 0)
            block_btn.hover_color = (230, 126, 34)

    # Dashboard Button Layout
    btn_start_y = dashboard.rect.top + 330
    btn_w = dash_w - 32
    btn_h = 32
    gap = 7

    btn_x = dash_x + 16

    # Row 1: Start & Pause
    dashboard.add_button(Button((btn_x, btn_start_y, btn_w // 2 - 4, btn_h), "Start", on_start, bg_color=(39, 174, 96), hover_color=(46, 204, 113)))
    dashboard.add_button(Button((btn_x + btn_w // 2 + 4, btn_start_y, btn_w // 2 - 4, btn_h), "Pause", on_pause, bg_color=(211, 84, 0), hover_color=(230, 126, 34)))

    # Row 2: Resume & Reset
    dashboard.add_button(Button((btn_x, btn_start_y + btn_h + gap, btn_w // 2 - 4, btn_h), "Resume", on_resume, bg_color=(41, 128, 185), hover_color=(52, 152, 219)))
    dashboard.add_button(Button((btn_x + btn_w // 2 + 4, btn_start_y + btn_h + gap, btn_w // 2 - 4, btn_h), "Reset", on_reset, bg_color=(127, 140, 141), hover_color=(149, 165, 166)))

    # Row 3: Speed & New Seed
    speed_btn = Button((btn_x, btn_start_y + (btn_h + gap) * 2, btn_w // 2 - 4, btn_h), f"Speed: {speed_levels[speed_idx]:.1f}x", on_cycle_speed, bg_color=(142, 68, 173), hover_color=(155, 89, 182))
    dashboard.add_button(speed_btn)
    dashboard.add_button(Button((btn_x + btn_w // 2 + 4, btn_start_y + (btn_h + gap) * 2, btn_w // 2 - 4, btn_h), "New Seed", on_new_seed, bg_color=(52, 73, 94), hover_color=(74, 105, 135)))

    # Row 4: Mode Switcher (Normal Crowd Flow vs Evacuation)
    mode_toggle_btn = Button((btn_x, btn_start_y + (btn_h + gap) * 3, btn_w, btn_h), "🚨 Trigger Evacuation", on_toggle_mode, bg_color=(192, 57, 43), hover_color=(231, 76, 60))
    dashboard.add_button(mode_toggle_btn)

    # Row 5: Dynamic Exit Blocking
    block_btn = Button((btn_x, btn_start_y + (btn_h + gap) * 4, btn_w, btn_h), "Block West Exit (Test Rerouting)", on_toggle_west_exit, bg_color=(211, 84, 0), hover_color=(230, 126, 34))
    dashboard.add_button(block_btn)

    font_banner = pygame.font.SysFont("Segoe UI", 20, bold=True)
    font_subbanner = pygame.font.SysFont("Segoe UI", 12)

    accumulated_ms = 0.0
    running = True

    while running:
        dt_ms = clock.tick(60)  # Render at smooth 60 FPS
        accumulated_ms += dt_ms

        current_speed = speed_levels[speed_idx]
        effective_interval = base_tick_delay_ms / current_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if engine.state == SimulationState.RUNNING:
                        engine.pause()
                    elif engine.state == SimulationState.PAUSED:
                        engine.resume()
                    elif engine.state in (SimulationState.STOPPED, SimulationState.COMPLETED):
                        if engine.state == SimulationState.COMPLETED:
                            engine.reset()
                        engine.start()
                elif event.key == pygame.K_r:
                    engine.reset()
                elif event.key == pygame.K_n:
                    engine.restart_with_new_seed()
                elif event.key == pygame.K_s:
                    on_cycle_speed()
                elif event.key == pygame.K_b:
                    on_toggle_west_exit()
                elif event.key == pygame.K_m:
                    on_toggle_mode()

            dashboard.handle_event(event)

        # Discrete simulation tick step (decoupled from render FPS)
        while accumulated_ms >= effective_interval:
            accumulated_ms -= effective_interval
            if engine.state == SimulationState.RUNNING:
                engine.step()

        # Render pass
        screen.fill((18, 22, 30))

        # Title bar
        title_font = pygame.font.SysFont("Segoe UI", 15, bold=True)
        title_mode_desc = "Normal Pedestrian Circulation" if engine.crowd_mode == CrowdMode.NORMAL_FLOW else "Emergency Egress"
        title_surf = title_font.render(
            f"{building.name} — [{title_mode_desc}]", True, (220, 225, 235)
        )
        screen.blit(title_surf, (margin_left, 12))

        # Render building & all 4 exits
        renderer.render_building(screen, blocked_exits=engine.blocked_exits)

        # Render crowd agents with continuous interpolation
        renderer.render_agents(
            screen,
            engine.manager.agents,
            is_evacuation_mode=(engine.crowd_mode == CrowdMode.EVACUATION)
        )

        # Render dashboard telemetry
        summary = engine.get_summary()
        dashboard.render(
            surface=screen,
            summary=summary,
            state=engine.state,
            crowd_mode=engine.crowd_mode,
            sim_speed=current_speed,
            is_west_exit_blocked=(0, 15) in engine.blocked_exits
        )

        # Evacuation completion banner
        if engine.state == SimulationState.COMPLETED and engine.crowd_mode == CrowdMode.EVACUATION:
            banner_rect = pygame.Rect(margin_left + 100, margin_top + grid_px_h // 2 - 50, grid_px_w - 200, 100)
            pygame.draw.rect(screen, (30, 40, 50), banner_rect, border_radius=8)
            pygame.draw.rect(screen, (46, 204, 113), banner_rect, width=2, border_radius=8)

            txt1 = font_banner.render("EVACUATION COMPLETE", True, (46, 204, 113))
            txt2 = font_subbanner.render(
                f"Evacuated {summary.evacuated_agents}/{summary.total_agents} in {summary.total_ticks} ticks | Avg: {summary.avg_evacuation_ticks:.1f} ticks",
                True, (230, 235, 240)
            )
            txt3 = font_subbanner.render("Press [R] to Reset or [M] for Normal Flow", True, (160, 175, 190))

            screen.blit(txt1, txt1.get_rect(center=(banner_rect.centerx, banner_rect.top + 26)))
            screen.blit(txt2, txt2.get_rect(center=(banner_rect.centerx, banner_rect.top + 54)))
            screen.blit(txt3, txt3.get_rect(center=(banner_rect.centerx, banner_rect.top + 76)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    create_simulation_app()
