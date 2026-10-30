"""Main application entry point for the Continuous Crowd Simulator.

Features:
  - Helbing Social Force Model continuous 2D vector physics.
  - Interactive Mouse Tools: Inspect Person, Drop Fire Hazard, Spawn Person.
  - 1-Click Preset Scenarios (Standard Evac, Fire Hazard Reroute, Normal Flow, High Density).
  - Real-Time Live Egress Curve Chart (Evacuated Population vs. Time).
  - Social Group Dynamics: Friends & pairs walking together with mutual cohesion.
  - Real-Time Dynamic Crowd Congestion Heatmap.
"""

import sys
import pygame
from environment.building import Building
from simulation.engine import SimulationEngine, SimulationState, CrowdMode
from visualization.renderer import BuildingRenderer
from visualization.dashboard import Dashboard, Button, MouseTool
from agents.agent import PanicLevel


def create_simulation_app() -> None:
    pygame.init()
    pygame.font.init()

    # Geometry setup
    grid_cols = 34
    grid_rows = 22
    cell_size = 24
    margin_left = 20
    margin_top = 40

    grid_px_w = grid_cols * cell_size
    grid_px_h = grid_rows * cell_size

    dash_x = margin_left + grid_px_w + 20
    dash_w = 340
    window_w = dash_x + dash_w + 20
    window_h = max(grid_px_h + margin_top + 50, 700)

    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("2D Continuous Crowd Simulator — Social Force Model & BFS")
    clock = pygame.time.Clock()

    building = Building.create_default(width=grid_cols, height=grid_rows)
    engine = SimulationEngine(building=building, agent_count=25, seed=42)
    renderer = BuildingRenderer(
        building=building,
        cell_size=cell_size,
        offset_x=margin_left,
        offset_y=margin_top
    )

    dashboard = Dashboard(
        x=dash_x,
        y=margin_top - 20,
        width=dash_w,
        height=window_h - margin_top + 10
    )

    # Simulation speed parameters
    speed_levels = [1.0, 2.0, 4.0, 0.5]
    speed_idx = 0
    base_tick_delay_ms = 40.0

    # Tool callbacks
    def set_tool_inspect() -> None:
        dashboard.active_tool = MouseTool.INSPECT
        tool_inspect_btn.is_active = True
        tool_hazard_btn.is_active = False
        tool_spawn_btn.is_active = False

    def set_tool_hazard() -> None:
        dashboard.active_tool = MouseTool.PLACE_HAZARD
        tool_inspect_btn.is_active = False
        tool_hazard_btn.is_active = True
        tool_spawn_btn.is_active = False

    def set_tool_spawn() -> None:
        dashboard.active_tool = MouseTool.SPAWN_PERSON
        tool_inspect_btn.is_active = False
        tool_hazard_btn.is_active = False
        tool_spawn_btn.is_active = True

    # Mode and state callbacks
    def on_start() -> None:
        engine.start()

    def on_pause() -> None:
        engine.pause()

    def on_resume() -> None:
        engine.resume()

    def on_reset() -> None:
        engine.reset()
        dashboard.graph.reset()

    def on_new_seed() -> None:
        engine.restart_with_new_seed()
        dashboard.graph.reset()

    def on_cycle_speed() -> None:
        nonlocal speed_idx
        speed_idx = (speed_idx + 1) % len(speed_levels)
        speed_btn.text = f"Speed: {speed_levels[speed_idx]:.1f}x"

    def on_toggle_mode() -> None:
        if engine.crowd_mode == CrowdMode.NORMAL_FLOW:
            engine.set_mode(CrowdMode.EVACUATION)
            mode_toggle_btn.text = "🏢 Normal Crowd Flow"
            mode_toggle_btn.bg_color = (39, 174, 96)
        else:
            engine.set_mode(CrowdMode.NORMAL_FLOW)
            mode_toggle_btn.text = "🚨 Trigger Evacuation"
            mode_toggle_btn.bg_color = (192, 57, 43)

    def on_toggle_heatmap() -> None:
        renderer.show_heatmap = not renderer.show_heatmap
        heatmap_btn.text = "Heatmap: ON" if renderer.show_heatmap else "Heatmap: OFF"
        heatmap_btn.bg_color = (241, 196, 15) if renderer.show_heatmap else (52, 73, 94)

    # Panic Modulator callbacks
    def set_calm() -> None:
        engine.set_panic(PanicLevel.CALM)
        calm_btn.is_active = True
        alert_btn.is_active = False
        panic_btn.is_active = False

    def set_alert() -> None:
        engine.set_panic(PanicLevel.ALERT)
        calm_btn.is_active = False
        alert_btn.is_active = True
        panic_btn.is_active = False

    def set_panic() -> None:
        engine.set_panic(PanicLevel.PANIC)
        calm_btn.is_active = False
        alert_btn.is_active = False
        panic_btn.is_active = True

    # Preset Benchmark Scenarios
    def load_scenario_standard() -> None:
        """Scenario 1: Standard Evacuation."""
        engine.reset()
        dashboard.graph.reset()
        engine.set_mode(CrowdMode.EVACUATION)
        engine.set_panic(PanicLevel.ALERT)
        mode_toggle_btn.text = "🏢 Normal Crowd Flow"
        mode_toggle_btn.bg_color = (39, 174, 96)
        engine.start()

    def load_scenario_fire_hazard() -> None:
        """Scenario 2: Fire Hazard with Live Rerouting."""
        engine.reset()
        dashboard.graph.reset()
        engine.set_mode(CrowdMode.EVACUATION)
        engine.set_panic(PanicLevel.PANIC)
        # Drop hazard blocking the west corridor
        engine.add_hazard(5, 14)
        engine.add_hazard(5, 15)
        mode_toggle_btn.text = "🏢 Normal Crowd Flow"
        mode_toggle_btn.bg_color = (39, 174, 96)
        engine.start()

    def load_scenario_normal_flow() -> None:
        """Scenario 3: Normal Daily Campus Circulation."""
        engine.reset()
        dashboard.graph.reset()
        engine.set_mode(CrowdMode.NORMAL_FLOW)
        engine.set_panic(PanicLevel.CALM)
        mode_toggle_btn.text = "🚨 Trigger Evacuation"
        mode_toggle_btn.bg_color = (192, 57, 43)
        engine.start()

    def load_scenario_high_density() -> None:
        """Scenario 4: High-Density Doorway Queuing Stress Test."""
        engine.reset()
        dashboard.graph.reset()
        engine.agent_count = 50
        engine.restart_with_new_seed(101)
        engine.set_mode(CrowdMode.EVACUATION)
        engine.set_panic(PanicLevel.ALERT)
        mode_toggle_btn.text = "🏢 Normal Crowd Flow"
        mode_toggle_btn.bg_color = (39, 174, 96)
        engine.start()

    # Build Dashboard UI layout
    btn_x = dash_x + 14
    btn_w = dash_w - 28
    btn_h = 24
    gap = 5
    btn_start_y = dashboard.rect.top + 325

    # Row 1: Mouse Tool Selection
    t_w = (btn_w - gap * 2) // 3
    tool_inspect_btn = Button((btn_x, btn_start_y, t_w, btn_h), "🔍 Inspect", set_tool_inspect, bg_color=(41, 128, 185))
    tool_inspect_btn.is_active = True
    tool_hazard_btn = Button((btn_x + t_w + gap, btn_start_y, t_w, btn_h), "🔥 Fire", set_tool_hazard, bg_color=(211, 84, 0))
    tool_spawn_btn = Button((btn_x + (t_w + gap) * 2, btn_start_y, t_w, btn_h), "➕ Person", set_tool_spawn, bg_color=(39, 174, 96))
    dashboard.add_button(tool_inspect_btn)
    dashboard.add_button(tool_hazard_btn)
    dashboard.add_button(tool_spawn_btn)

    # Row 2: Panic Level Modulator
    p_y = btn_start_y + btn_h + gap
    calm_btn = Button((btn_x, p_y, t_w, btn_h), "😌 Calm", set_calm, bg_color=(46, 204, 113))
    calm_btn.is_active = True
    alert_btn = Button((btn_x + t_w + gap, p_y, t_w, btn_h), "🏃 Alert", set_alert, bg_color=(241, 196, 15), text_color=(20, 24, 32))
    panic_btn = Button((btn_x + (t_w + gap) * 2, p_y, t_w, btn_h), "🚨 Panic", set_panic, bg_color=(231, 76, 60))
    dashboard.add_button(calm_btn)
    dashboard.add_button(alert_btn)
    dashboard.add_button(panic_btn)

    # Row 3: Preset Benchmark Scenarios (1-click demonstrations)
    s_y = p_y + btn_h + gap
    sc_w = (btn_w - gap) // 2
    dashboard.add_button(Button((btn_x, s_y, sc_w, btn_h), "⚡ Scenario 1: Evac", load_scenario_standard, bg_color=(41, 128, 185)))
    dashboard.add_button(Button((btn_x + sc_w + gap, s_y, sc_w, btn_h), "🔥 Scenario 2: Hazard", load_scenario_fire_hazard, bg_color=(211, 84, 0)))

    s_y2 = s_y + btn_h + gap
    dashboard.add_button(Button((btn_x, s_y2, sc_w, btn_h), "🚶 Scenario 3: Flow", load_scenario_normal_flow, bg_color=(39, 174, 96)))
    dashboard.add_button(Button((btn_x + sc_w + gap, s_y2, sc_w, btn_h), "👥 Scenario 4: Density", load_scenario_high_density, bg_color=(142, 68, 173)))

    # Row 4: Mode Switcher & Heatmap Toggle
    m_y = s_y2 + btn_h + gap
    mode_toggle_btn = Button((btn_x, m_y, btn_w // 2 - 3, btn_h), "🚨 Trigger Evacuation", on_toggle_mode, bg_color=(192, 57, 43))
    heatmap_btn = Button((btn_x + btn_w // 2 + 3, m_y, btn_w // 2 - 3, btn_h), "Heatmap: OFF", on_toggle_heatmap, bg_color=(52, 73, 94))
    dashboard.add_button(mode_toggle_btn)
    dashboard.add_button(heatmap_btn)

    # Row 5: Playback Controls (Start, Pause, Resume, Reset)
    c_y = m_y + btn_h + gap
    c_w = (btn_w - gap * 3) // 4
    dashboard.add_button(Button((btn_x, c_y, c_w, btn_h), "Start", on_start, bg_color=(39, 174, 96)))
    dashboard.add_button(Button((btn_x + c_w + gap, c_y, c_w, btn_h), "Pause", on_pause, bg_color=(211, 84, 0)))
    dashboard.add_button(Button((btn_x + (c_w + gap) * 2, c_y, c_w, btn_h), "Resume", on_resume, bg_color=(41, 128, 185)))
    dashboard.add_button(Button((btn_x + (c_w + gap) * 3, c_y, c_w, btn_h), "Reset", on_reset, bg_color=(127, 140, 141)))

    # Row 6: Speed & Respawn Seed
    sp_y = c_y + btn_h + gap
    speed_btn = Button((btn_x, sp_y, btn_w // 2 - 3, btn_h), f"Speed: {speed_levels[speed_idx]:.1f}x", on_cycle_speed, bg_color=(142, 68, 173))
    dashboard.add_button(speed_btn)
    dashboard.add_button(Button((btn_x + btn_w // 2 + 3, sp_y, btn_w // 2 - 3, btn_h), "New Seed", on_new_seed, bg_color=(52, 73, 94)))

    accumulated_ms = 0.0
    running = True

    while running:
        dt_ms = clock.tick(60)
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
                            dashboard.graph.reset()
                        engine.start()
                elif event.key == pygame.K_m:
                    on_toggle_mode()
                elif event.key == pygame.K_h:
                    on_toggle_heatmap()
                elif event.key == pygame.K_r:
                    on_reset()
                elif event.key == pygame.K_n:
                    on_new_seed()
                elif event.key == pygame.K_1:
                    set_calm()
                elif event.key == pygame.K_2:
                    set_alert()
                elif event.key == pygame.K_3:
                    set_panic()

            # Mouse interaction on Building floor plan
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if (margin_left <= mx <= margin_left + grid_px_w and
                    margin_top <= my <= margin_top + grid_px_h):
                    gx, gy = renderer.pixel_to_grid(mx, my)

                    if dashboard.active_tool == MouseTool.INSPECT:
                        target_agent = engine.manager.find_agent_near(gx, gy, max_dist=1.2)
                        engine.manager.selected_agent = target_agent
                    elif dashboard.active_tool == MouseTool.PLACE_HAZARD:
                        engine.add_hazard(int(gx), int(gy))
                    elif dashboard.active_tool == MouseTool.SPAWN_PERSON:
                        engine.spawn_agent_at(gx, gy)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Right click on a hazard to remove it
                mx, my = event.pos
                if (margin_left <= mx <= margin_left + grid_px_w and
                    margin_top <= my <= margin_top + grid_px_h):
                    gx, gy = renderer.pixel_to_grid(mx, my)
                    engine.remove_hazard(int(gx), int(gy))

            dashboard.handle_event(event)

        # Continuous physics integration
        while accumulated_ms >= effective_interval:
            accumulated_ms -= effective_interval
            if engine.state == SimulationState.RUNNING:
                engine.step(dt=0.04)

        # Rendering
        screen.fill((16, 20, 28))

        # Title
        title_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        mode_label = "Everyday Circulation" if engine.crowd_mode == CrowdMode.NORMAL_FLOW else "Emergency Egress"
        screen.blit(
            title_font.render(f"{building.name} — [{mode_label}]", True, (220, 225, 235)),
            (margin_left, 12)
        )

        # Render building & exits
        renderer.render_building(screen, blocked_exits=engine.blocked_exits)

        # Optional density heatmap
        renderer.render_density_heatmap(screen, engine.manager.agents)

        # Render continuous agents & inspector reticle
        renderer.render_agents(
            screen,
            engine.manager.agents,
            selected_agent=engine.manager.selected_agent,
            is_evacuation_mode=(engine.crowd_mode == CrowdMode.EVACUATION)
        )

        # Render dashboard telemetry, live graph & inspector dossier
        summary = engine.get_summary()
        dashboard.render(
            surface=screen,
            summary=summary,
            state=engine.state,
            crowd_mode=engine.crowd_mode,
            sim_speed=current_speed,
            selected_agent=engine.manager.selected_agent,
            is_heatmap_active=renderer.show_heatmap
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    create_simulation_app()
