def test_provider_manager_routes():
    from src.services.providers import ProviderManager
    pm = ProviderManager()
    resp = pm.route_text_task("sentiment", {"text": "this is great"})
    assert isinstance(resp, dict)
