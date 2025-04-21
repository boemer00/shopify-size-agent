from enum import Enum
from typing import Dict, Any, Optional, List, Union


class State(str, Enum):
    """
    States for the conversation flow
    """
    INIT = "INIT"  # Initial state
    CONFIRMATION = "CONFIRMATION"  # Asked if size is correct
    SIZING_QUESTIONS = "SIZING_QUESTIONS"  # Asked about sizing info
    RECOMMENDATION = "RECOMMENDATION"  # Made a recommendation
    CONFIRMED = "CONFIRMED"  # Size confirmed
    COMPLETE = "COMPLETE"  # Conversation complete


class Event(str, Enum):
    """
    Events that can trigger state transitions
    """
    START = "START"  # Start conversation
    CONFIRM = "CONFIRM"  # Customer confirmed
    DENY = "DENY"  # Customer denied/unsure
    INFO_PROVIDED = "INFO_PROVIDED"  # Customer provided sizing info
    RECOMMENDATION_ACCEPTED = "RECOMMENDATION_ACCEPTED"  # Customer accepted recommendation
    RECOMMENDATION_REJECTED = "RECOMMENDATION_REJECTED"  # Customer rejected recommendation


class StateMachine:
    """
    A simple state machine to manage conversation flow
    """

    def __init__(self):
        # Define the state transitions
        self.transitions = {
            State.INIT: {
                Event.START: State.CONFIRMATION
            },
            State.CONFIRMATION: {
                Event.CONFIRM: State.CONFIRMED,
                Event.DENY: State.SIZING_QUESTIONS
            },
            State.SIZING_QUESTIONS: {
                Event.INFO_PROVIDED: State.RECOMMENDATION
            },
            State.RECOMMENDATION: {
                Event.RECOMMENDATION_ACCEPTED: State.CONFIRMED,
                Event.RECOMMENDATION_REJECTED: State.SIZING_QUESTIONS
            },
            State.CONFIRMED: {
                Event.START: State.COMPLETE
            }
        }

    def get_next_state(self, current_state: State, event: Event) -> Optional[State]:
        """
        Get the next state based on the current state and event

        Args:
            current_state: The current state
            event: The event that occurred

        Returns:
            The next state, or None if the transition is not defined
        """
        if current_state not in self.transitions:
            return None

        if event not in self.transitions[current_state]:
            return None

        return self.transitions[current_state][event]

    def get_available_events(self, current_state: State) -> List[Event]:
        """
        Get the available events for the current state

        Args:
            current_state: The current state

        Returns:
            A list of available events
        """
        if current_state not in self.transitions:
            return []

        return list(self.transitions[current_state].keys())


def map_intent_to_event(intent: str, entities: Dict[str, Any]) -> Event:
    """
    Map an intent to a state machine event

    Args:
        intent: The detected intent
        entities: The detected entities

    Returns:
        The corresponding event
    """
    if intent == "CONFIRM":
        return Event.CONFIRM
    elif intent in ["UNSURE", "CHANGE_SIZE"]:
        return Event.DENY
    elif intent == "OTHER" and (entities.get("usual_size") or entities.get("height") or entities.get("weight")):
        return Event.INFO_PROVIDED

    # Default to DENY if no clear mapping
    return Event.DENY


def determine_phase_from_state(state: State) -> str:
    """
    Determine the conversation phase from the state

    Args:
        state: The current state

    Returns:
        The conversation phase
    """
    if state == State.CONFIRMATION:
        return "CONFIRMATION"
    elif state == State.SIZING_QUESTIONS:
        return "SIZING_QUESTIONS"
    elif state == State.RECOMMENDATION:
        return "RECOMMENDATION"
    elif state in [State.CONFIRMED, State.COMPLETE]:
        return "COMPLETE"
    else:
        return "CONFIRMATION"  # Default
