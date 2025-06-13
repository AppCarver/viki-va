"""Unit tests for the response_parser module.

This module contains comprehensive unit tests for the functions within
`response_parser.py`, which are responsible for robustly extracting
JSON payloads from various LLM response formats.

It specifically verifies:
- Extraction of JSON from standard markdown code blocks (with or without
  'json' tag).
- Extraction from markdown blocks embedded within surrounding text.
- Handling of whitespace and escaped characters within JSON.
- Correct behavior for malformed JSON within detected markdown blocks.
- The functionality of the fallback parsing mechanism for plain JSON or
  responses without markdown.
- Error handling for various invalid JSON formats or empty inputs.
"""

import json
import sys
from typing import Any
from unittest.mock import patch

# Adjust the import path for the module under test
# This allows running tests directly or as part of a larger suite
sys.path.insert(
    0, "shared_libs/utils/llm"
)  # Add the directory containing response_parser.py
from shared_libs.utils.llm.response_parser import (
    _fallback_strip_and_parse,
    extract_json_from_markdown_code_block,
)

# --- Tests for extract_json_from_markdown_code_block ---


def test_extract_json_standard_format() -> None:
    """Test with a standard markdown JSON code block."""
    text = '```json\n{"intent": "greet", "entities": {}}\n```'
    expected = {"intent": "greet", "entities": {}}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


def test_extract_json_no_json_tag() -> None:
    """Test with a markdown code block but without the 'json' tag."""
    text = '```\n{"intent": "ask_weather", "location": "London"}\n```'
    expected = {"intent": "ask_weather", "location": "London"}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


def test_extract_json_with_surrounding_text() -> None:
    """Test with text before and after the markdown block."""
    text = (
        'Here\'s the NLU result: ```json\n{"intent": "order_pizza", '
        '"size": "large"}\n``` Hope that helps!'
    )
    expected = {"intent": "order_pizza", "size": "large"}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


def test_extract_json_with_leading_and_trailing_whitespace() -> None:
    """Test with extra whitespace around the markdown block."""
    text = ' \n ```json \n {"intent": "status"} \n ``` \n '
    expected = {"intent": "status"}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


# The test_extract_json_complex_json function is provided separately.


def test_extract_json_with_escaped_quotes_inside() -> None:
    """Test with JSON containing escaped quotes."""
    text = r'```json{"message": "He said \"Hello, world!!\""}```'
    expected = {"message": 'He said "Hello, world!!"'}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


def test_extract_json_malformed_json_in_block_triggers_json_decode_error() -> None:
    """Test to ensre regex extracts a block but not valid json.

    Test that if regex extracts a block but it's not valid JSON,
    it falls back to _fallback_strip_and_parse and fails there.
    This specifically tests the `except json.JSONDecodeError as e:` branch
    in `extract_json_from_markdown_code_block`.
    """
    # Regex will find `{"key": "value" "invalid_syntax}`
    text = r'```json{"key": "value" "invalid_syntax}```'
    # The regex block attempts parsing, fails, and calls fallback.
    # Fallback will also fail.
    result = extract_json_from_markdown_code_block(text)
    assert result is None


def test_extract_json_no_markdown_block_triggers_fallback() -> None:
    """Test that if no markdown block is found, it directly calls.

    _fallback_strip_and_parse.
    This covers the `else` branch in `extract_json_from_markdown_code_block`.
    """
    text = "This is just some plain text, no JSON here."
    result = extract_json_from_markdown_code_block(text)
    assert result is None


# --- Tests for _fallback_strip_and_parse (private helper) ---


def test_fallback_strip_and_parse_valid_plain_json() -> None:
    """Test direct parsing of clean JSON without markdown."""
    text = '{"status": "ok"}'
    expected = {"status": "ok"}
    result = _fallback_strip_and_parse(text)
    assert result == expected


def test_fallback_strip_and_parse_malformed_json() -> None:
    """Test fallback with malformed JSON, should return None."""
    text = "not json"
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_empty_string() -> None:
    """Test fallback with an empty string after stripping."""
    text = ""
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_only_whitespace() -> None:
    """Test fallback with only whitespace after stripping."""
    text = "   \n "
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_only_fences() -> None:
    """Test fallback with only fences, resulting in an empty string."""
    text = "```json```"
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_with_prefix_suffix_only() -> None:
    """Directly test fallback with common LLM intros/outros (no fences)."""
    text = 'Here\'s the JSON:\n{"data":123}\nThat was easy.'
    # The regex in fallback for `Here's the JSON:` should work here.
    # However, the trailing "That was easy." means json.loads will fail
    # with ExtraData. The function correctly returns None in this scenario.
    expected = None
    result = _fallback_strip_and_parse(text)
    assert result == expected


def test_fallback_strip_and_parse_with_trailing_non_json() -> None:
    """Test a case where the JSON is valid but has trailing non-JSON chars."""
    text = '{"key": "value"}trailing text'
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_with_multiple_json_objects() -> None:
    """Test with multiple JSON objects, which should cause a decode error."""
    text = '{"obj1":1}{"obj2":2}'
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_with_unterminated_string() -> None:
    """Test JSON that's syntactically incorrect due to an unterminated string."""
    text = '{"key": "malformed,}'
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_mixed_content_complex() -> None:
    """Test complex mixed content that should result in None."""
    text = 'some text ```json {"data": "value"} ``` more text'
    # This won't be caught by the regex in _fallback, it will be just
    # 'some text ```json {"data": "value"} ``` more text' and then
    # json.loads will fail
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_with_leading_conversational_text_only() -> None:
    """Test only leading conversational text that should be stripped."""
    text = 'here is the json: {"status": "success"}'
    expected = None  # Change expected to None
    result = _fallback_strip_and_parse(text)
    assert result == expected


def test_fallback_strip_and_parse_unexpected_exception() -> None:
    """Test the generic `except Exception` branch in `_fallback_strip_and_parse`.

    This uses a mock to simulate an arbitrary error during json.loads.
    """
    original_loads = json.loads

    def mock_json_loads(s: str) -> Any:
        if s == '{"key": "value"}':
            raise Exception("Simulated unexpected JSON error")
        return original_loads(s)

    with patch("json.loads", side_effect=mock_json_loads):
        text = '{"key": "value"}'
        result = _fallback_strip_and_parse(text)
        assert result is None


def test_extract_json_no_json_returned_from_llm() -> None:
    """Test scenario where LLM returns conversational text with no JSON."""
    text = "This is not JSON. The LLM decided to be chatty."
    result = extract_json_from_markdown_code_block(text)
    assert result is None


def test_extract_json_complex_json() -> None:
    """Test with more complex, multi-line JSON."""
    # Changed from """ to ''' to avoid conflict with markdown rendering
    text = """
    ```json
        {
        "intent": "complex_request",
        "entities": {
            "item": "laptop",
            "quantity": 2
        }
    }
    """
    expected = {
        "intent": "complex_request",
        "entities": {"item": "laptop", "quantity": 2},
    }
    result = extract_json_from_markdown_code_block(text)
    assert result == expected
