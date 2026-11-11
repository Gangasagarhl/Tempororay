from itertools import cycle

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


class ReplayChatModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


agent = create_agent(
    ReplayChatModel(messages=cycle([AIMessage(content="Hello from replay mode.")])),
    tools=[],
)
