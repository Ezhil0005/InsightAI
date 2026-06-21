def test_multilingual_detection():
    from src.services.language_service import detect_language
    assert detect_language("Hello world")["language"] == "en"
    assert detect_language("हेलो दुनिया")["language"] == "hi"
