"""Tests for rate limiting."""


def test_rate_limit_allows_normal_usage(client):
    """Normal usage should not be rate limited."""
    for _ in range(5):
        resp = client.get('/api/health')
        assert resp.status_code == 200


def test_get_actions_rate_limit(client):
    """Exceeding rate limit returns 429."""
    payload = {'provider': 'ollama', 'user_request': 'test'}
    responses = []
    for _ in range(25):
        resp = client.post('/api/get-actions', json=payload)
        responses.append(resp.status_code)

    # At least some should be rate-limited (429)
    assert 429 in responses
