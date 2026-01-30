"""Backend API tests."""
import json


def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert 'providers' in data


def test_providers_endpoint(client):
    resp = client.get('/api/providers')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'providers' in data
    assert isinstance(data['providers'], list)
    names = [p['name'] for p in data['providers']]
    assert 'Ollama (Local)' in names


def test_get_actions_missing_request(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'ollama', 'screenshot': '', 'ui_tree': {}})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_get_actions_invalid_provider(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'nonexistent', 'user_request': 'test'})
    assert resp.status_code == 400


def test_get_actions_request_too_long(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'ollama', 'user_request': 'x' * 6000})
    assert resp.status_code == 400


def test_add_provider_missing_id(client):
    resp = client.post('/api/add-provider', json={})
    assert resp.status_code == 400


def test_add_provider_cannot_overwrite_builtin(client):
    resp = client.post('/api/add-provider', json={'id': 'openai', 'config': {}})
    assert resp.status_code == 400


def test_add_provider_success(client):
    resp = client.post('/api/add-provider',
                       json={'id': 'custom_test', 'config': {'endpoint': 'http://example.com'}})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_capture_no_service(client, monkeypatch):
    """If automation service doesn't exist, capture returns error."""
    monkeypatch.setattr('os.path.exists', lambda p: False)
    resp = client.post('/api/capture', json={'action': 'capture'})
    assert resp.status_code == 500
