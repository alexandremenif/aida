from typing import Callable, List, Generator
from conversation.types import State


Agent = Callable[[State], State]


def create_conversation(state: State, agents: List[Agent]) -> Generator[State, None, None]:
    # Run an infinite loop where each agent is called in a sequence.
    # New states are yielded only when they are different from the previous state.
    # If no agent in the sequence changes the state, it means that a fixed point has been reached and the loop can be
    # broken (the conversation is over).
    while True:
        sequence_initial_state = state
        for agent in agents:
            new_state = agent(state)
            if new_state != state:
                yield new_state
            state = new_state
        if state == sequence_initial_state:
            break
