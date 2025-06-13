# shared_libs/utils/llm/response_parser.py

"""Utility functions for parsing and cleaning LLM responses.

This module provides robust methods to extract structured JSON content
from strings that may contain markdown code block wrappers or other
unrelated conversational text, often found in Large Language Model (LLM)
outputs.
"""

import json
import re
from typing import Any

# Regex to find a JSON-like block enclosed in markdown code fences.
# - ```(?:json)? : Matches '```' optionally followed by 'json'.
#                   (?:...) creates a non-capturing group.
# - \s* : Matches any whitespace (including newlines) zero or more times.
# - (\{.*?\})   : CAPTURES a string starting with '{', followed by any
#                 characters (non-greedy), and ending with '}'.
#                 This is our potential JSON payload.
# - \s* : Matches any trailing whitespace.
# - ```         : Matches the closing '```'.
# re.DOTALL     : Ensures '.' also matches newlines, allowing multi-line JSON.
MARKDOWN_JSON_REGEX = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_from_markdown_code_block(
    text: str,
) -> dict[str, Any] | None:
    """Attempt to extract and parse JSON from markdown code block.

    This function prioritizes robust regex extraction. If the regex fails to find
    a markdown code block, or if the extracted block is not valid JSON, it
    falls back to simpler string stripping (removeprefix/removesuffix).

    Args:
        text: The input string, typically an LLM response containing JSON.

    Returns:
        A dictionary representing the JSON object if successfully extracted
        and parsed. Returns None if no valid JSON can be extracted or parsed.

    """
    json_data = None
    extracted_json_str = None

    # 1. Attempt robust extraction using regex
    match = MARKDOWN_JSON_REGEX.search(text)
    if match:  # This is the start of a branch to cover (line ~55 in your report)
        extracted_json_str = match.group(1)
        print(f"DEBUG: Regex extracted potential JSON: {extracted_json_str[:200]}...")
        try:
            json_data = json.loads(extracted_json_str)
        except json.JSONDecodeError as e:
            print(">>> DEBUG_COVERAGE: Hitting JSONDecodeError in regex block <<<")
            print(
                f"WARNING: Regex successfully extracted a block, but it's not "
                f"valid JSON. Error: {e}. Attempting fallback stripping. "
                f"Problematic string start: '{extracted_json_str[:100]}...'"
            )
            # If regex found something but it's not valid JSON, try the fallback
            json_data = _fallback_strip_and_parse(text)
    else:  # This is the 'else' branch to cover (line ~68)
        print(">>> DEBUG_COVERAGE: Hitting NO MARKDOWN BLOCK found <<<")
        print(
            "DEBUG: No markdown JSON code block found using regex. "
            "Attempting fallback stripping."
        )
        # If regex didn't find any markdown block, go straight to fallback
        json_data = _fallback_strip_and_parse(text)

    return json_data


def _fallback_strip_and_parse(text: str) -> dict[str, Any] | None:
    """Private helper: Parse JSON after simple markdown stripping.

    This is a less robust fallback.

    Args:
        text: The input string.

    Returns:
        A dictionary representing the JSON object, or None if parsing fails.

    """
    # Make sure to remove common variations for robustness
    stripped_text = (
        text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    )

    # Also attempt to strip common LLM conversational intros/outros if they exist
    stripped_text = re.sub(
        r"^(?:Here's the JSON:|```json|```)\s*", "", stripped_text, flags=re.IGNORECASE
    ).strip()
    stripped_text = re.sub(
        r"\s*(?:```)$", "", stripped_text, flags=re.IGNORECASE
    ).strip()

    if not stripped_text:  # This is the 'if' branch to cover (line ~103)
        print(">>> DEBUG_COVERAGE: Hitting EMPTY STRIPPED TEXT in fallback <<<")
        print("DEBUG: Fallback stripping resulted in an empty string.")
        return None

    try:
        json_data = json.loads(stripped_text)
        print(">>> DEBUG_COVERAGE: Hitting SUCCESSFUL fallback parse <<<")
        print("DEBUG: Fallback stripping successfully parsed JSON.")
        if isinstance(json_data, dict):
            return json_data
        else:
            return None
    except json.JSONDecodeError as e:
        print(">>> DEBUG_COVERAGE: Hitting JSONDecodeError in fallback <<<")
        print(
            f"ERROR: Fallback stripping also failed to parse JSON from LLM response. "
            f"Error: {e}. Problematic string start: '{stripped_text[:100]}...'"
        )
        return None
    except Exception as e:  # This is the 'except' branch to cover (line ~116)
        print(">>> DEBUG_COVERAGE: Hitting UNEXPECTED EXCEPTION in fallback <<<")
        print(
            f"ERROR: An unexpected error occurred during fallback JSON parsing: {e}. "
            f"String start: '{stripped_text[:100]}...'"
        )
        return None
