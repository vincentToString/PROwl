from intake.main import ping, health


def test_ping_route():
    response = ping()
    assert isinstance(response, dict)
    assert response.get("message") == "hello world"


def test_health_route():
    response = health()
    assert isinstance(response, dict)
    assert response.get("status") == "healthy"
