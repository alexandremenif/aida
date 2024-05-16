from typing import Protocol, List, TypeVar
from conversation.messages import Message

Self = TypeVar('Self', bound='ConversationState')


class ConversationState(Protocol):
    messages: List[Message]

    def append_message(self: Self, message: Message) -> Self:
        ...


State = TypeVar('State', bound=ConversationState)