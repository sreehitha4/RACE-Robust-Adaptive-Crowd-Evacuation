from fastapi.testclient import TestClient

from server.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_simulation_controls():
    with TestClient(app) as client:
        assert client.post("/api/simulation/start").json()["status"] == "running"
        assert client.get("/api/simulation/status").json()["status"] == "running"
        assert client.post("/api/simulation/pause").json()["status"] == "paused"
        assert client.post("/api/simulation/reset").json()["status"] == "reset"


def test_websocket_sends_environment_then_frame():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/simulation") as websocket:
            environment = websocket.receive_json()
            frame = websocket.receive_json()

        assert environment["type"] == "environment"
        assert environment["width"] == 20.0
        assert frame["type"] == "frame"
        assert frame["total_agents"] == 24
        assert len(frame["agents"]) == 24


def test_reset_restores_population():
    with TestClient(app) as client:
        client.post("/api/simulation/start")
        client.post("/api/simulation/reset")
        with client.websocket_connect("/ws/simulation") as websocket:
            websocket.receive_json()
            frame = websocket.receive_json()
        assert frame["simulation_time"] == 0
        assert frame["evacuated"] == 0
        assert frame["total_agents"] == 24
