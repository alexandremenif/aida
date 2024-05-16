from typing import List, Iterable, Callable

from conversation.agent import Agent
from conversation.messages import Message, AssistantMessage, SystemMessage
from conversation.tool import Tool
from conversation.types import State


class LLM:

    def __call__(self, messages: List[Message], tools: Iterable[Tool]) -> AssistantMessage:
        ...


class LLMAgent(Agent[State]):

    def __init__(
            self,
            llm: LLM,
            prompt: str,
            tools: Iterable[Tool],
            condition: Callable[[State], bool] = lambda state: True
    ):
        self.llm = llm
        self.prompt = prompt
        self.tools = tools
        self.condition = condition

    def __call__(self, state: State) -> State:
        # If the condition is satisfied, ask the model for a completion.
        if self.condition(state):
            message = self.llm(
                [SystemMessage(self.prompt), *state.messages],
                self.tools
            )

            return state.append_message(message)

        # If the condition is not satisfied, return the state unchanged.
        return state
