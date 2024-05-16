from typing import Iterable, List
from openai.types.chat import ChatCompletionMessageParam
from conversation.llm import LLM
from conversation.messages import Message, UserMessage, SystemMessage, ToolMessage, AssistantMessage
from conversation.tool import Tool
from openai import OpenAI


class OpenAIModel(LLM):

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def __call__(self, messages: List[Message], tools: Iterable[Tool]) -> AssistantMessage:
        def create_chat_completion_message(message: Message) -> ChatCompletionMessageParam:
            match message:
                case UserMessage(content=content):
                    return ChatCompletionMessageParam(role='user', content=content)
                case SystemMessage(content=content):
                    return ChatCompletionMessageParam(role='system', content=content)
                case ToolMessage(content=content, tool_call_id=tool_call_id):
                    return ChatCompletionMessageParam(role='tool', content=content, tool_call_id=tool_call_id)
                case AssistantMessage(content=content, tool_calls=tool_calls):
                    return ChatCompletionMessageParam(role='assistant', content=content, tool_calls=tool_calls)

        response = self.client.chat.completions.create(
            model=self.model,
            tools=[tool.openai_schema() for tool in tools],
            messages=[create_chat_completion_message(message) for message in messages]
        )

        # We only care about the first choice.
        message = response.choices[0].message

        return AssistantMessage(content=message.content, tool_calls=message.tool_calls)
