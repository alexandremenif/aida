import json
from typing import TypeVar, Type, Callable

from pydantic import BaseModel

from conversation.agent import Agent
from conversation.messages import ToolMessage, AssistantMessage
from conversation.types import State

T = TypeVar('T', bound=BaseModel)


class Tool[T](Callable[[T], str]):

    def __init__(self, name: str, description: str, parameters_type: Type[T], function: Callable[[T], str]):
        self.name = name
        self.description = description
        self.parameters_type = parameters_type
        self.function = function

    def openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_type.model_json_schema()
            }
        }


class ToolAgent(Agent[State]):

    def __init__(self, tool: Tool):
        self.tool = tool

    def __call__(self, state: State) -> State:
        last_message = state.messages[-1] if state.messages else None

        match last_message:
            case AssistantMessage(tool_calls=tool_calls) if tool_calls is not None:
                # For every tool call that match the tool name, validate the parameters, call the function and append
                # the result to the conversation state.
                for tool_call in last_message.tool_calls:
                    if tool_call.function.name == self.tool.name:
                        try:
                            self.tool.parameters_type.parse_obj(json.loads(tool_call.function.arguments))
                            state = state.append_message(
                                ToolMessage(content=self.tool.function(tool_call.function), tool_call_id=tool_call.id)
                            )
                        except Exception as e:
                            state = state.append_message(
                                ToolMessage(content=f'Error: {e}', tool_call_id=tool_call.id)
                            )
                return state
            case _:
                # This is not a tool call, return the state unchanged.
                return state
