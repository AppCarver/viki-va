"""The ActionExecutor component for the Viki Virtual Assistant.

This component is responsible for taking the NLU-processed intent and
entities and dispatching them to the appropriate functions or modules that
can fulfill the user's request. It acts as a router, mapping recognized
intents to specific actions within Viki's capabilities.
"""

import logging
from datetime import datetime, tzinfo
from typing import Any

import pytz

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Dispatches actions based on identified intents and entities."""

    # Define Viki's name as a class attribute
    VIKI_NAME = "Viki"

    def __init__(self) -> None:
        """Initialize the ActionExecutor."""
        logger.info("ActionExecutor initialized.")

    def _get_time_for_location(self, location: str) -> str:
        """Get the current time for a specified location."""
        timezone_map = {
            "paris": "Europe/Paris",
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "berlin": "Europe/Berlin",
            "united states": "America/New_York",
            "usa": "America/New_York",
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
            tz: tzinfo = pytz.timezone(timezone_str)
            utc_now: datetime = datetime.now(pytz.utc)
            local_time: datetime = utc_now.astimezone(tz)

            return local_time.strftime("%H:%M:%S on %A, %B %d, %Y")

        except pytz.exceptions.UnknownTimeZoneError:
            return (
                f"I don't recognize the timezone for '{location}'. "
                "Please try a different city."
            )
        except Exception as e:
            logger.error("ERROR in _get_time_for_location: %s", e, exc_info=True)
            return "I encountered an error trying to get the time for that location."

    def _handle_get_name(self) -> dict[str, Any]:
        """Handle the 'get_name' intent."""
        return {
            "success": True,
            "result_data": {
                "message": f"My name is {self.VIKI_NAME}.",
                "viki_name": self.VIKI_NAME,
                "dialogue_act": "inform_name",
            },
            "error": None,
        }

    # Renamed/Refactored from the previous 'execute_action'
    def execute_action_and_get_structured_response(
        self, intent: Any, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute an action based on the given intent and entities.

        Args:
        ----
            intent (Any): The identified intent from the NLU service.
                          Expected to be a string or a dict like
                          {'name': 'intent_name', 'confidence': ...}.
            entities (Dict[str, Any]): A dictionary of extracted entities.

        Returns:
        -------
            Dict[str, Any]: A dictionary containing the outcome of the action execution,
                            following the standardized format.
                            {
                                "success": bool,
                                "result_data": Dict[str, Any],
                                "error": Dict[str, Any] | None
                            }

        """
        # Extract the intent name correctly, handling both string and dict formats
        # We'll prioritize the 'name' key if the intent is a dictionary.
        intent_name: str
        if isinstance(intent, dict) and "name" in intent:
            intent_name = intent["name"]
        elif isinstance(intent, str):
            intent_name = intent
        else:
            # Handle unexpected intent format
            logger.error(f"Received unexpected intent format: {intent}")
            return {
                "success": False,
                "result_data": None,
                "error": {
                    "code": "INVALID_INTENT_FORMAT",
                    "message": "ActionExecutor received an unparseable intent format.",
                    "details": f"Intent: {intent}",
                },
            }

        logger.debug(
            f"ActionExecutor received intent: '{intent_name}' with entities: {entities}"
        )

        # Map intents to dialogue_acts and prepare response_content
        # All checks below should now use 'intent_name'
        if intent_name == "greet":  # MODIFIED LINE
            user_name = entities.get("user_name")
            return {
                "success": True,
                "result_data": {
                    "dialogue_act": "greet",
                    "user_name": user_name,
                    "message": f"Hello{' ' + user_name if user_name else ''}!",
                },
                "error": None,
            }

        elif intent_name == "get_name":  # MODIFIED LINE
            return self._handle_get_name()

        elif intent_name == "tell_joke":  # MODIFIED LINE
            return {
                "success": True,
                "result_data": {
                    "dialogue_act": "tell_joke",
                    "joke_punchline": "Why don't scientists trust atoms? "
                    "Because they make up everything!",
                    "message": "Why don't scientists trust atoms? "
                    "Because they make up everything!",
                },
                "error": None,
            }

        elif intent_name == "get_time":  # MODIFIED LINE
            location = entities.get("location")
            if location:
                time_str = self._get_time_for_location(str(location))
                if (
                    "I'm not sure" in time_str
                    or "I don't recognize" in time_str
                    or "error" in time_str
                ):
                    return {
                        "success": False,
                        "result_data": None,
                        "error": {
                            "code": "TIME_ERROR",
                            "message": time_str,
                            "details": f"Failed to get time for {location}",
                        },
                    }
                else:
                    return {
                        "success": True,
                        "result_data": {
                            "dialogue_act": "inform_time",
                            "time": time_str,
                            "location": location,
                            "message": f"The current time in {location} is {time_str}.",
                        },
                        "error": None,
                    }
            else:
                utc_now_str: str = datetime.now(pytz.utc).strftime("%H:%M:%S UTC")
                return {
                    "success": False,
                    "result_data": None,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "Please specify a location to get the time.",
                        "details": f"Missing 'location' entity for 'get_time' intent. "
                        f"Current UTC: {utc_now_str}",
                    },
                }

        elif intent_name == "unknown":  # MODIFIED LINE
            raw_query = entities.get("raw_query", "")
            return {
                "success": False,
                "result_data": None,
                "error": {
                    "code": "UNKNOWN_INTENT",
                    "message": "I'm sorry, I don't understand that request.",
                    "details": f"Received unknown intent. Raw query: '{raw_query}'",
                },
            }

        elif intent_name == "farewell":  # MODIFIED LINE
            return {
                "success": True,
                "result_data": {
                    "dialogue_act": "farewell",
                    "message": "Goodbye! It was nice talking to you.",
                },
                "error": None,
            }

        else:
            # Default fallback for unimplemented but recognized intents
            return {
                "success": False,
                "result_data": None,
                "error": {
                    "code": "UNIMPLEMENTED_ACTION",
                    "message": f"I know the intent '{intent_name}', "
                    "but I don't have a specific action implemented for it yet.",
                    "details": f"Intent: {intent}, Entities: {entities}",
                },
            }
