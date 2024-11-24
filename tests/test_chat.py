import pytest
from src.chat import generate_response
import os

@pytest.fixture
def valid_query():
    return "What is AI?"

@pytest.fixture
def invalid_query():
    return ""
# Test environment variables
def test_api_key_availability():
    assert os.getenv("GROQ_API_KEY"), "GROQ_API_KEY is not set!"
    assert os.getenv("LANGCHAIN_API_KEY"), "LANGCHAIN_API_KEY is not set!"

def test_generate_response_valid_query(valid_query):
    response = generate_response(valid_query)
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_empty_query(invalid_query):
    response = generate_response(invalid_query)
    assert response == "I cannot process an empty query. Please provide some input."

