import pytest
from unittest.mock import MagicMock
from models.domain import Script
from services.topic_generator import GroqTopicGenerator
from services.script_generator import GroqScriptGenerator
from core.exceptions import QuotaExceededError, GenerationError
from config.settings import settings

# Mocking the CostGuard to avoid limits being reached across tests
@pytest.fixture(autouse=True)
def reset_cost_guard(monkeypatch):
    import core.cost_guard
    core.cost_guard.cost_guard.groq_requests = 0
    monkeypatch.setattr(settings, "groq_api_key", "mock_key")

def test_topic_generator_success(mocker):
    mock_groq = mocker.patch("services.topic_generator.Groq")
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    mock_message = MagicMock()
    mock_message.content = "The Future of AI"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    gen = GroqTopicGenerator()
    topic = gen.generate_topic(["Old Topic 1"])
    assert topic == "The Future of AI"

def test_script_generator_success(mocker):
    mock_groq = mocker.patch("services.script_generator.Groq")
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    # Mock valid JSON response
    mock_json = '{"segments": [{"text": "Hello world."}, {"text": "Subscribe."}]}'
    mock_message = MagicMock()
    mock_message.content = mock_json
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    gen = GroqScriptGenerator()
    script = gen.generate_script("AI")
    
    assert isinstance(script, Script)
    assert len(script.segments) == 2
    assert script.segments[0].text == "Hello world."
    assert script.segments[1].text == "Subscribe."

def test_script_generator_invalid_json(mocker):
    mock_groq = mocker.patch("services.script_generator.Groq")
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    
    # Mock invalid JSON response
    mock_message = MagicMock()
    mock_message.content = "This is not JSON"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    gen = GroqScriptGenerator()
    with pytest.raises(GenerationError):
        gen.generate_script("AI")
