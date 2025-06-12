"""The ActionExecutor component for the Viki Virtual Assistant.

This component is responsible for taking the NLU-processed intent and
entities and dispatching them to the appropriate functions or modules that
can fulfill the user's request. It acts as a router, mapping recognized
intents to specific actions within Viki's capabilities.
"""

from datetime import datetime, tzinfo
from typing import Any

import pytz


class ActionExecutor:
    """Dispatches actions based on identified intents and entities."""

    def __init__(self) -> None:
        """Initialize the ActionExecutor."""
        print("ActionExecutor initialized.")  # Consider replacing with logging

    def _get_time_for_location(self, location: str) -> str:
        """Get the current time for a specified location."""
        timezone_map = {
            "paris": "Europe/Paris",
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "berlin": "Europe/Berlin",
            "united states": "America/New_York",  # Added for completeness
            "usa": "America/New_York",  # Added for completeness
        }

        normalized_location = location.lower()
        timezone_str: str | None = timezone_map.get(normalized_location)

        if not timezone_str:
            for key, tz_name in timezone_map.items():
                if normalized_location in key:
                    timezone_str = tz_name
                    break

        if not timezone_str:
            # Return a simple string for now, will be wrapped in NLG later
            return (
                f"I'm not sure about the timezone for '{location}'. "
                "Can you be more specific?"
            )

        try:
            tz: tzinfo = pytz.timezone(timezone_str)
            utc_now: datetime = datetime.now(pytz.utc)
            local_time: datetime = utc_now.astimezone(tz)

            # Format for direct inclusion in NLG content, or for easier parsing
            return local_time.strftime("%H:%M:%S on %A, %B %d, %Y")

        except pytz.exceptions.UnknownTimeZoneError:
            return (
                f"I don't recognize the timezone for '{location}'. "
                "Please try a different city."
            )
        except Exception as e:
            print(f"ERROR in _get_time_for_location: {e}")  # Replace with logging
            return "I encountered an error trying to get the time for that location."

    # Renamed/Refactored from the previous 'execute_action'
    def execute_action_and_get_structured_response(
        self, intent: str, entities: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Execute an action based on the given intent and entities.

        Args:
            intent (str): The identified intent from the NLU service.
            entities (Dict[str, Any]): A dictionary of extracted entities.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - dialogue_act (str):
                    The high-level communicative act Viki needs to perform.
                - response_content (Dict[str, Any]):
                    Data needed by NLG to form the response.

        """
        print(
            f"DEBUG: ActionExecutor received intent: "
            f"'{intent}' with entities: {entities}"
        )

        # Map intents to dialogue_acts and prepare response_content
        if intent == "greet":
            user_name = entities.get("user_name")  # NLU might extract this
            return "greet", {"user_name": user_name} if user_name else {}

        elif intent == "tell_joke":
            # For a joke, the NLG will use the 'joke_punchline' to form the full joke
            return "tell_joke", {
                "joke_punchline": "Why don't scientists trust atoms? "
                "Because they make up everything!"
            }

        elif intent == "get_time":
            location = entities.get("location")
            if location:
                time_str = self._get_time_for_location(str(location))
                # If _get_time_for_location returns an error message,
                # we pass it to NLG to include in the response.
                if (
                    "I'm not sure" in time_str
                    or "I don't recognize" in time_str
                    or "error" in time_str
                ):
                    return "inform_error", {"error_message": time_str}
                else:
                    return "inform_time", {"time": time_str, "location": location}
            else:
                utc_now_str: str = datetime.now(pytz.utc).strftime("%H:%M:%S UTC")
                return "ask_for_clarification", {
                    "missing_info": "location for time",
                    "current_utc_time": utc_now_str,
                }

        elif intent == "unknown":
            raw_query = entities.get("raw_query", "")
            return "unknown_intent_response", {"raw_query": raw_query}

        elif intent == "farewell":
            return "farewell", {}

        # Default fallback if intent is understood but no specific action
        # is implemented yet
        else:
            return "unimplemented_action", {"intent": intent}
