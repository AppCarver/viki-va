# services/action_executor/src/action_executor.py

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
        print("ActionExecutor initialized.")

    def _get_time_for_location(self, location: str) -> str:
        """Get the current time for a specified location."""
        timezone_map = {
            "paris": "Europe/Paris",
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "berlin": "Europe/Berlin",
        }

        normalized_location = location.lower()
        timezone_str: str | None = timezone_map.get(normalized_location)

        if not timezone_str:
            for key, tz_name in timezone_map.items():
                if normalized_location in key:
                    timezone_str = tz_name
                    break

        if not timezone_str:
            return (
                f"I'm not sure about the timezone for '{location}'. "
                "Can you be more specific?"
            )

        try:
            # Removed 'type: ignore' as MyPy should now infer correctly
            tz: tzinfo = pytz.timezone(timezone_str)
            # Removed 'type: ignore' as MyPy should now infer correctly
            utc_now: datetime = datetime.now(pytz.utc)
            local_time: datetime = utc_now.astimezone(tz)

            return (
                f"The current time in {location} is "
                f"{local_time.strftime('%H:%M:%S on %A, %B %d, %Y')}."
            )
        except pytz.exceptions.UnknownTimeZoneError:
            return (
                f"I don't recognize the timezone for '{location}'. "
                "Please try a different city."
            )
        except Exception as e:
            print(f"ERROR in _get_time_for_location: {e}")
            return "I encountered an error trying to get the time for that location."

    def execute_action(self, intent: str, entities: dict[str, Any]) -> str:
        """Execute an action based on the given intent and entities.

        Args:
        ----
            intent (str): The identified intent from the NLU service.
            entities (Dict[str, Any]): A dictionary of extracted entities.

        Returns:
        -------
            str: A simple placeholder response string indicating the action
                 taken. In a real application, this would trigger actual
                 functionality and return a more meaningful response (e.g., a
                 joke, the time).

        """
        print(f"ActionExecutor received intent: '{intent}' with entities: {entities}")

        if intent == "greet":
            return "Hello there! How can I help you today?"
        elif intent == "tell_joke":
            return "Why don't scientists trust atoms? Because they make up everything!"
        elif intent == "get_time":
            location = entities.get("location")
            if location:
                return self._get_time_for_location(str(location))
            else:
                utc_now_str: str = datetime.now(pytz.utc).strftime(
                    "The current UTC time is %H:%M:%S."
                )
                return (
                    f"You asked for the time, but didn't specify a location. "
                    f"{utc_now_str}"
                )
        elif intent == "unknown":
            return (
                "I'm sorry, I didn't quite understand that. Could you please rephrase?"
            )
        else:
            return (
                f"I understand you want to '{intent}', but I don't have "
                "an action for that yet."
            )
