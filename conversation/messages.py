from dataclasses import dataclass


@dataclass
class UserMessage:
    content: str


@dataclass
class SystemMessage:
    content: str


@dataclass
class Function:
    arguments: str
    name: str


@dataclass
class ToolCall:
    id: str
    function: Function


@dataclass
class AssistantMessage:
    content: str | None
    tool_calls: list[ToolCall] | None


@dataclass
class ToolMessage:
    content: str
    tool_call_id: str


type Message = UserMessage | SystemMessage | AssistantMessage | ToolMessage
