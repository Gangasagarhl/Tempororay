"""Stage 0 test: can recorded answers drive a real tool-calling agent, offline?"""
import os

os.environ["LANGSMITH_TRACING"] = "false"

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

tool_ran_with = []


class ReplayChatModel(GenericFakeChatModel):
    """Plays back recorded answers and accepts tools like a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


@tool
def get_weather(city: str) -> str:
    """Return the weather for a city."""
    tool_ran_with.append(city)
    return f"It is sunny in {city}."


recorded = iter([
    AIMessage(content="", tool_calls=[
        {"name": "get_weather", "args": {"city": "Paris"}, "id": "call_1", "type": "tool_call"},
    ]),
    AIMessage(content="The weather in Paris is sunny."),
])

agent = create_agent(ReplayChatModel(messages=recorded), tools=[get_weather])
result = agent.invoke({"messages": [{"role": "user", "content": "Weather in Paris?"}]})

for message in result["messages"]:
    print(f"{type(message).__name__}: content={message.content!r} "
          f"tool_calls={getattr(message, 'tool_calls', None)}")
print("real tool actually ran with:", tool_ran_with)
assert tool_ran_with == ["Paris"]
assert result["messages"][-1].content == "The weather in Paris is sunny."
print("REPLAY SPIKE PASSED")
