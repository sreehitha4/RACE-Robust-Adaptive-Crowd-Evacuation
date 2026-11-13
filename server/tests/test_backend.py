from fastapi.testclient import TestClient
from server.main import app


def test_health_and_ml_status():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        ml = client.get("/api/v1/ml/status")
        assert ml.status_code == 200
        assert ml.json()["prediction_input"] == [8, 2]
        assert ml.json()["prediction_output"] == [12, 2]


def test_live_websocket_contract_and_controls():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/simulation") as ws:
            environment = ws.receive_json()
            frame = ws.receive_json()
            assert environment["type"] == "environment"
            assert frame["type"] == "frame"
            assert "agents" in frame
        assert client.post("/api/simulation/start").status_code == 200
        assert client.post("/api/simulation/pause").status_code == 200
        assert client.post("/api/simulation/reset").status_code == 200


def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "race_http_requests_total" in response.text or "python_gc_objects_collected_total" in response.text


def test_ml_prediction_endpoint_uses_real_checkpoint():
    with TestClient(app) as client:
        response = client.post("/api/v1/ml/predict", json={"observed_positions": [[i * 0.1, i * 0.05] for i in range(8)]})
        assert response.status_code == 200
        prediction = response.json()["prediction"]
        assert len(prediction) == 12
        assert all(len(point) == 2 for point in prediction)


def test_model_registry_candidate_activation():
    with TestClient(app) as client:
        models = client.get("/api/v1/ml/models")
        assert models.status_code == 200
        assert any(item["model_id"] == "trajectory_lstm_best" for item in models.json()["models"])
        activated = client.post("/api/v1/ml/models/trajectory_lstm_best/activate")
        assert activated.status_code == 200
        assert activated.json()["active"] is True


def test_simulation_loop_advances_and_emits_metrics():
    import time
    with TestClient(app) as client:
        assert client.post("/api/simulation/start").status_code == 200
        time.sleep(0.65)
        status = client.get("/api/simulation/status").json()
        assert status["simulation_time"] >= 0.3
        metrics = client.get("/metrics").text
        assert "race_simulation_step_seconds_count" in metrics
        assert client.post("/api/simulation/pause").status_code == 200
