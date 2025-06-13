"""Unit tests for the LLM response parsing utility."""

from unittest.mock import patch

from shared_libs.utils.llm.response_parser import (
    _fallback_strip_and_parse,  # We need this for one of the new tests
    extract_json_from_markdown_code_block,
)

# --- Test Cases for Successful Extraction (Primary Regex Path) ---


def test_extract_json_standard_format():
    """Verify standard markdown code block with 'json' tag is extracted."""
    text = '```json\n{"intent": "greet", "entities": {}}\n```'
    expected = {"intent": "greet", "entities": {}}
    assert extract_json_from_markdown_code_block(text) == expected


def test_extract_json_no_json_tag():
    """Verify markdown code block without 'json' tag is extracted."""
    text = '```\n{"intent": "ask_weather", "location": "London"}\n```'
    expected = {"intent": "ask_weather", "location": "London"}
    assert extract_json_from_markdown_code_block(text) == expected


def test_extract_json_with_surrounding_text():
    """Verify markdown block with intro and outro text is handled correctly."""
    text = (
        "Here's the NLU result: ```json\n"
        '{"intent": "order_pizza", "size": "large"}\n'
        "``` Hope that helps!"
    )
    expected = {"intent": "order_pizza", "size": "large"}
    assert extract_json_from_markdown_code_block(text) == expected


def test_extract_json_with_leading_trailing_whitespace_in_block():
    """Verify JSON block with extra whitespace inside fences is parsed."""
    text = '```json   {"intent": "status"}   ```'
    expected = {"intent": "status"}
    assert extract_json_from_markdown_code_block(text) == expected


def test_extract_json_multi_line_json():
    """Verify multi-line JSON structure within fences is extracted."""
    text = (
        "```json\n"
        "{\n"
        '  "intent": "complex_request",\n'
        '  "entities": {\n'
        '    "item": "laptop",\n'
        '    "quantity": 2\n'
        "  }\n"
        "}\n"
        "```"
    )
    expected = {
        "intent": "complex_request",
        "entities": {"item": "laptop", "quantity": 2},
    }
    assert extract_json_from_markdown_code_block(text) == expected


def test_extract_json_complex_inner_content_escaped_quotes():
    """Verify JSON with escaped quotes inside values is parsed."""
    text = '```json\n{"message": "He said \\"Hello, world!\\""}\n```'
    expected = {"message": 'He said "Hello, world!"'}
    assert extract_json_from_markdown_code_block(text) == expected


# --- Test Cases for Fallback and Failure Scenarios ---


def test_extract_json_malformed_json_in_block_triggers_json_decode_error():
    """Verify that JSONDecodeError and fallback triggered.

    For malformed JSON inside a markdown block triggers JSONDecodeError and falls back
    to fallback_strip_and_parse.
    This specifically targets lines 55-62 in `extract_json_from_markdown_code_block`.
    """
    # This input is correctly fenced markdown, but the content is NOT valid JSON.
    text = (
        "```json\n"
        '{"key": "value" "invalid_syntax}\n'  # Missing comma, extra quote
        "```"
    )
    result = extract_json_from_markdown_code_block(text)
    # The regex will match, but json.loads will fail, leading to fallback.
    # The fallback also won't parse this, so the final result is None.
    assert result is None


def test_extract_json_no_markdown_fences_plain_json_success_fallback():
    """Verify plain JSON string without markdown fences succeeds via fallback.

    This targets lines 107-109 in `_fallback_strip_and_parse` (success path).
    """
    text = '{"status": "success", "data": "plain"}'
    expected = {"status": "success", "data": "plain"}
    result = extract_json_from_markdown_code_block(text)
    assert result == expected


def test_extract_json_no_markdown_fences_not_json_fails_fallback():
    """Verify plain text without markdown fences fails via fallback."""
    text = "This is just some plain text, no JSON here."
    result = extract_json_from_markdown_code_block(text)
    assert result is None


def test_extract_json_empty_string():
    """Verify empty input string returns None."""
    result = extract_json_from_markdown_code_block("")
    assert result is None


def test_extract_json_only_fences_no_content_regex_match_but_empty_json():
    """Verify string with only markdown fences and no content returns None.

    This ensures the regex captures an empty string, which `json.loads`
    will reject, causing a fallback.
    """
    text = "```json\n\n```"  # Fences with only newlines inside
    result = extract_json_from_markdown_code_block(text)
    assert result is None


def test_extract_json_only_fences_and_whitespace_regex_match_but_whitespace_json():
    """Verify string with fences and only whitespace inside returns None.

    This ensures the regex captures whitespace, which `json.loads`
    will reject, causing a fallback.
    """
    text = "```   ```"  # Fences with spaces inside
    result = extract_json_from_markdown_code_block(text)
    assert result is None


# --- Test Cases for Fallback Logic Directly (Targeting specific lines) ---


def test_fallback_strip_and_parse_standard_json():
    """Directly test fallback with plain JSON.

    This specifically targets lines 107-109 (success path) in
    `_fallback_strip_and_parse`.
    """
    text = '{"key": "value"}'
    expected = {"key": "value"}
    result = _fallback_strip_and_parse(text)
    assert result == expected


def test_fallback_strip_and_parse_with_prefix_suffix_only():
    """Directly test fallback with common LLM intros/outros (no fences)."""
    text = 'Here\'s the JSON:\n{"data":123}\nThat was easy.'
    # The regex in fallback for `Here's the JSON:` should work here.
    expected = None
    result = _fallback_strip_and_parse(text)
    assert result == expected


def test_fallback_strip_and_parse_with_complex_fences_and_extra_text_fails():
    """Directly test fallback with complex string that it should fail to parse."""
    text = 'Here\'s the JSON:\n```json\n{"data":123}\n```\nSome concluding remarks.'
    result = _fallback_strip_and_parse(text)
    # This input is too complex for the simple fallback stripping, should fail
    assert result is None


def test_fallback_strip_and_parse_malformed_json():
    """Directly test fallback with malformed JSON."""
    text = '{"key": "malformed,'
    result = _fallback_strip_and_parse(text)
    assert result is None


def test_fallback_strip_and_parse_results_in_empty_string_after_stripping():
    """Test _fallback_strip_and_parse when input becomes empty after stripping.

    This explicitly covers lines 103-104 (if not stripped_text: return None).
    """
    test_cases = [
        "  ",  # Only whitespace
        "",  # Empty string
        # These are processed by _fallback_strip_and_parse, and should result
        # in an empty string after all the .removeprefix/.removesuffix and .strip()
        "```json\n   \n```",
        "  \n ``` \n  ",
        "here is the json:\n   \n",
    ]
    for text_input in test_cases:
        result = _fallback_strip_and_parse(text_input)
        assert result is None, (
            f"Expected None for input '{text_input}', but got {result}"
        )


def test_fallback_strip_and_parse_unexpected_exception_during_json_loads():
    """Test _fallback_strip_and_parse for an unexpected exception during json.loads.

    This explicitly covers lines 116-121 (`except Exception as e:` block).
    """
    # Patch json.loads globally to ensure it affects the function under test
    with patch("json.loads") as mock_json_loads:
        # Configure the mock to raise a non-JSONDecodeError (e.g., ValueError)
        mock_json_loads.side_effect = ValueError("Simulated unexpected JSON error")

        # Provide a string that would normally be valid JSON,
        # but our mocked json.loads will raise an unexpected exception.
        text_input = '{"key": "value"}'

        result = _fallback_strip_and_parse(text_input)

        # Verify that json.loads was called with the stripped text
        mock_json_loads.assert_called_once_with(text_input)

        # The function should catch the ValueError and return None
        assert result is None, (
            "Expected None due to mocked unexpected exception, but got a result."
        )


def test_extract_json_no_json_curly_braces_in_regex_catch_all_miss():
    """Test fallback when '{' not found.

    Test that if the regex finds a block that doesn't start with '{'
    it won't match, leading to fallback. This specifically covers the regex
    pattern not matching (a 'miss' for the regex itself).
    """
    text = "```json\nThis is not JSON.\n```"
    # The regex MARKDOWN_JSON_REGEX = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```"
    # specifically looks for '{' at the start of the capture group.
    # So this input will NOT match the regex.
    result = extract_json_from_markdown_code_block(text)
    assert result is None  # Fallback will also fail for this string.
