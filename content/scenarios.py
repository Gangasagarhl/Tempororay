"""Hand-written core simulations. Each step is one press of Next."""

SIMS = []


def st(h, t, a=None, l=None, s=None):
    step = {"h": h, "t": t}
    if a:
        step["a"] = list(a)
    if l:
        step["l"] = [l, l] if isinstance(l, int) else list(l)
    if s:
        step["s"] = s
    return step


def sim(key, module, title, intro, actors, code, steps, quiz=None, beta=False, lang="python"):
    item = {"key": key, "module": module, "title": title, "intro": intro, "actors": actors,
            "code": code, "steps": steps, "lang": lang, "beta": beta, "kind": "Core simulation"}
    if quiz:
        item["quiz"] = {"q": quiz[0], "a": quiz[1], "c": quiz[2], "why": quiz[3]}
    SIMS.append(item)


USER, PY, LC, MODEL, TOOL = "You", "Your Python", "LangChain", "Model", "Tool"

# ---------- Module 0 ----------
sim("api", "m0", "What actually happens in an API call",
    "An API call is one program sending a message to another program and waiting for the answer.",
    [PY, "Internet", "Server"],
    'import requests\n\nurl = "https://api.example.com/v1/weather"\nheaders = {"x-api-key": "my-secret"}\nparams = {"city": "Paris"}\n\nreply = requests.get(url, headers=headers, params=params)\nprint(reply.status_code)\nprint(reply.json())',
    [st("Choose the address", "Every API job has its own web address, called an endpoint. This line stores it. Nothing has been sent yet.", l=3, s={"url": "https://api.example.com/v1/weather"}),
     st("Prepare your ID card", "The server needs to know who is asking. A header is a small note attached to the message. Here it carries your API key.", l=4, s={"headers": {"x-api-key": "my-secret"}}),
     st("Say what you want", "Parameters are the details of your order. You want the weather for Paris.", l=5, s={"params": {"city": "Paris"}}),
     st("The message leaves your computer", "Python packs the address, the header and the details into one request and sends it. `GET` means “please give me something.”", ("Your Python", "Internet", "GET /v1/weather?city=Paris"), l=7),
     st("The message arrives", "The server receives the request. Your program is now waiting and doing nothing else on this line.", ("Internet", "Server", "GET /v1/weather?city=Paris"), l=7),
     st("The server checks and works", "First it checks the key. If the key is wrong it stops and sends back `401`. Here the key is fine, so it looks up the weather.", ("Server", "Server"), l=7),
     st("The answer comes back", "The server replies with a number that says how it went, and the data as JSON.", ("Server", "Your Python", "200 {temp: 18}"), l=7, s={"reply.status_code": 200, "reply.json()": {"city": "Paris", "temp_c": 18}}),
     st("Your program continues", "Line 8 prints `200`, which means success. Line 9 prints the data. That is all an API call is: send a message, wait, read the answer.", l=(8, 9))],
    ("What does a 401 response most often mean?", ["The city was not found", "Your key or login was not accepted", "The answer is still being made"], 1, "401 means the server could not confirm who you are."))

sim("llm", "m0", "How a model writes an answer",
    "A model does not look up answers. It writes one small piece at a time, each time picking a likely next piece.",
    ["Your text", "Tokenizer", "Model", "Answer"], "",
    [st("You send text", "You send: “The sky is”. To a model this is not yet anything it can read.", ("Your text", "Tokenizer", "The sky is"), s={"input": "The sky is"}),
     st("Text becomes tokens", "The text is cut into small pieces called tokens. You are usually billed by how many tokens go in and come out.", ("Tokenizer", "Model", "[The][ sky][ is]"), s={"tokens_in": ["The", " sky", " is"]}),
     st("The model scores every next piece", "The model gives a score to each possible next token. It does not know facts the way a database does. It knows patterns.", ("Model", "Model"), s={"next_guess": {" blue": 0.71, " clear": 0.12, " falling": 0.01}}),
     st("One token is picked", "A likely token is chosen and added to the answer.", ("Model", "Answer", " blue"), s={"answer": " blue"}),
     st("The whole thing repeats", "The model looks at everything again, now including “ blue”, and scores the next token.", ("Model", "Model"), s={"next_guess": {".": 0.64, " today": 0.2}}),
     st("It stops", "This repeats until the model writes a stop signal or reaches a length limit.", ("Model", "Answer", "."), s={"answer": " blue.", "tokens_out": 2}),
     st("Why this matters", "The model only sees what you send in that one request. It has no memory of earlier requests unless your program sends them again. Almost everything in LangChain exists to manage this.")],
    ("A model remembers your last request on its own.", ["True", "False"], 1, "Each request stands alone. Your program must send the history again."))

sim("agentloop", "m0", "What makes a program an agent",
    "An agent is a loop: the model decides, your program acts, and the result goes back to the model.",
    [USER, "Loop", MODEL, TOOL], "",
    [st("You ask", "“What is the weather in Paris?” The model has no way of seeing today's weather by itself.", (USER, "Loop", "Weather in Paris?"), s={"messages": ["user: Weather in Paris?"]}),
     st("The model gets the question and a tool list", "The loop sends your question along with a description of the tools available.", ("Loop", MODEL, "messages + tool list")),
     st("The model decides", "The model does not run the tool. It writes a request: “please run get_weather with city=Paris.”", (MODEL, "Loop", "tool call"), s={"messages": ["user: Weather in Paris?", "ai: call get_weather(Paris)"]}),
     st("Your program runs the tool", "The loop runs the real Python function.", ("Loop", TOOL, "city=Paris")),
     st("The result joins the conversation", "The tool result is added to the list of messages.", (TOOL, "Loop", "Sunny, 18C"), s={"messages": ["user: Weather in Paris?", "ai: call get_weather(Paris)", "tool: Sunny, 18C"]}),
     st("The model looks again", "Everything is sent back to the model, including the tool result.", ("Loop", MODEL, "all 3 messages")),
     st("The model finishes", "This time the model needs no tool, so it writes a normal answer. No tool request means the loop ends.", (MODEL, "Loop", "It is sunny, 18C"), s={"messages": ["user: Weather in Paris?", "ai: call get_weather(Paris)", "tool: Sunny, 18C", "ai: It is sunny, 18C"]}),
     st("You get the answer", "That is the whole idea of an agent. Everything else is about controlling this loop.", ("Loop", USER, "It is sunny, 18C"))],
    ("Who actually runs the tool?", ["The model", "Your program", "The provider's website"], 1, "The model only asks. Your program runs the function."))

sim("map", "m0", "The whole LangChain family in one story",
    "Five names cause most of the confusion. Follow one agent through them.",
    ["LangChain", "LangGraph", "Deep Agents", "LangSmith"], "",
    [st("LangChain: write the agent", "LangChain is the toolkit for writing an agent: models, tools, messages and the agent loop.", ("LangChain", "LangChain")),
     st("LangGraph: the engine underneath", "An agent made by LangChain runs on LangGraph. LangGraph controls order, saving progress and pausing for a person.", ("LangChain", "LangGraph", "runs on")),
     st("Deep Agents: a bigger ready-made agent", "Deep Agents adds planning, files, helpers and long-term memory on top, for long jobs.", ("LangGraph", "Deep Agents", "built on")),
     st("LangSmith: watch, test and run it", "LangSmith is a separate online platform. It records what your agent did, tests it, and can host it. It works with other frameworks too.", ("Deep Agents", "LangSmith", "traces")),
     st("Managed Deep Agents", "This is a Deep Agent described as a project folder that LangSmith runs for you."),
     st("The four stages", "Everything fits four stages: **Build** (LangChain, LangGraph, Deep Agents), **Test** (evaluation), **Deploy** (hosting) and **Monitor** (tracing). The Agent Registry lists every agent and ties them together.")],
    ("Which one records what your agent did?", ["LangGraph", "LangSmith", "Deep Agents"], 1, "LangSmith is the platform for tracing, testing and hosting."))

sim("pipeline", "m0", "Behind the scenes: how a background job runs",
    "This shows how a script on your PC could hand work to a free OpenCode model and check the result.",
    ["Claude", "Script", "OpenCode", "Free model", "Checks"], "",
    [st("The rules are set", "Claude writes the instructions and the pass or fail rules once.", ("Claude", "Script", "instructions")),
     st("The script starts a job", "The script starts the `opencode run` command, just as if it had been typed in a terminal.", ("Script", "OpenCode", "opencode run -m free-model")),
     st("OpenCode calls the model", "OpenCode sends the job to its servers, which run the free model.", ("OpenCode", "Free model", "job")),
     st("Text comes back", "The model only returns text. It cannot touch your files.", ("Free model", "OpenCode", "answer text")),
     st("The script saves and checks", "The script saves the text and runs automatic tests, which cost nothing.", ("OpenCode", "Checks", "lesson"), s={"checks": "running"}),
     st("Pass or fail", "A pass is kept. A fail goes back to the model up to three times.", ("Checks", "Script", "pass"), s={"checks": "pass"}),
     st("Claude reads a summary", "Claude reads only a short report, which is how the cost stays low.", ("Script", "Claude", "status report")),
     st("What happened when the limit hit", "OpenCode's free allowance ran out during testing, so this lab's simulations were built directly from the saved docs, API specs and package code instead.")])

# ---------- Module 1 ----------
sim("invoke", "m1", "model.invoke(): one question, one answer",
    "The smallest possible LangChain program.",
    [PY, LC, MODEL],
    'from langchain.chat_models import init_chat_model\n\nmodel = init_chat_model("anthropic:claude-sonnet-5-5", temperature=0)\nreply = model.invoke("What is an API? One sentence.")\n\nprint(reply.content)\nprint(reply.usage_metadata)',
    [st("Bring in the helper", "This loads `init_chat_model`, a function that can create a chat model for many providers.", l=1),
     st("Create the model object", "The text before the colon names the provider, and the rest names the model. No request is sent yet. This only creates an object that knows how to call that model.", (PY, LC, "provider + name"), l=3, s={"model": "ChatAnthropic(temperature=0)"}),
     st("You call invoke", "`invoke` means “run this and wait for the whole answer.”", (PY, LC, "text"), l=4),
     st("Your text becomes a message", "LangChain turns the string into a proper user message, because chat models work on lists of messages.", (LC, LC), l=4, s={"messages": [{"role": "user", "content": "What is an API? One sentence."}]}),
     st("The real request goes out", "LangChain translates this into the exact format this provider expects and sends it.", (LC, MODEL, "HTTP request"), l=4),
     st("The provider answers", "The answer comes back in the provider's own format.", (MODEL, LC, "provider reply"), l=4),
     st("LangChain standardises it", "Whatever the provider, you get the same kind of object: an `AIMessage`. This is why you can switch providers by changing one string.", (LC, PY, "AIMessage"), l=4, s={"reply.content": "An API lets programs talk to each other.", "reply.usage_metadata": {"input_tokens": 14, "output_tokens": 9, "total_tokens": 23}}),
     st("Read the answer", "`content` holds the text and `usage_metadata` holds the token counts.", l=(6, 7))],
    ("What does the first line of model creation send to the provider?", ["The prompt", "Nothing yet", "Your token count"], 1, "Creating the object sends nothing. `invoke` sends the request."))

sim("messages", "m1", "Messages: how a conversation is really stored",
    "A conversation is simply a Python list that your program keeps growing.",
    [PY, MODEL],
    'from langchain_core.messages import SystemMessage, HumanMessage\n\nhistory = [\n    SystemMessage("You are a short, kind tutor."),\n    HumanMessage("My name is Asha."),\n]\nreply = model.invoke(history)\nhistory.append(reply)\n\nhistory.append(HumanMessage("What is my name?"))\nreply = model.invoke(history)',
    [st("Standing instructions", "A system message tells the model how to behave for the whole conversation.", l=4, s={"history": ["system: You are a short, kind tutor."]}),
     st("Your first message", "A human message is what the user said.", l=5, s={"history": ["system: You are a short, kind tutor.", "human: My name is Asha."]}),
     st("Send the list", "The full list goes to the model.", (PY, MODEL, "2 messages"), l=7),
     st("Answer arrives", "The answer is an AI message.", (MODEL, PY, "Nice to meet you!"), l=7, s={"reply": "ai: Nice to meet you, Asha!"}),
     st("You must keep it", "If you skip this line, the model will never know it said this. Your program owns the memory.", l=8, s={"history": ["system: You are a short, kind tutor.", "human: My name is Asha.", "ai: Nice to meet you, Asha!"]}),
     st("Next question", "The new question is added to the list.", l=10, s={"history": ["system: You are a short, kind tutor.", "human: My name is Asha.", "ai: Nice to meet you, Asha!", "human: What is my name?"]}),
     st("All 4 messages are sent again", "This is how the model “remembers”: it is shown the whole history every time. Longer history means more tokens and more cost.", (PY, MODEL, "4 messages"), l=11),
     st("It can answer", "The name was in the list it just received.", (MODEL, PY, "Your name is Asha."), l=11, s={"reply": "ai: Your name is Asha."})],
    ("How does a chat model appear to remember?", ["It saves your account's history", "The whole history is sent with each request", "It searches the web"], 1, "The list of messages is sent again on every request."))

sim("toolcall", "m1", "Tools: what the model really receives and returns",
    "A tool is an ordinary function plus a description the model can read.",
    [PY, LC, MODEL, TOOL],
    'from langchain.tools import tool\n\n@tool\ndef get_weather(city: str) -> str:\n    """Get the current weather for a city."""\n    return f"Sunny in {city}"\n\nwith_tools = model.bind_tools([get_weather])\nreply = with_tools.invoke("Weather in Paris?")\n\nprint(reply.tool_calls)\nresult = get_weather.invoke(reply.tool_calls[0])',
    [st("Turn a function into a tool", "`@tool` reads the function's name, inputs and docstring to build a description.", l=(3, 6), s={"get_weather.name": "get_weather", "get_weather.description": "Get the current weather for a city.", "get_weather.args": {"city": "string"}}),
     st("Tell the model it exists", "`bind_tools` attaches the description to future requests. Nothing has run.", l=8, s={"with_tools": "model + 1 tool description"}),
     st("The model gets a menu", "The request contains your question and the tool's description. It does **not** contain your Python code.", (LC, MODEL, "question + description"), l=9),
     st("The model answers with a request", "Instead of text, the model returns a structured request naming the tool and inputs.", (MODEL, LC, "tool_calls"), l=9, s={"reply.tool_calls": [{"name": "get_weather", "args": {"city": "Paris"}, "id": "call_1"}]}),
     st("Nothing has run yet", "Printing shows only the request. The model cannot run code. It is your program's decision to run it.", l=11),
     st("Your program runs the function", "Now the real Python function runs, with the inputs the model chose.", (PY, TOOL, "city=Paris"), l=12),
     st("You get a ToolMessage", "The output is wrapped in a `ToolMessage` linked by `id` to the request, ready to give back to the model.", (TOOL, PY, "Sunny in Paris"), l=12, s={"result": {"type": "ToolMessage", "content": "Sunny in Paris", "tool_call_id": "call_1"}})],
    ("Why does a good docstring matter?", ["Python requires it", "The model reads it to decide when to use the tool", "It makes the tool faster"], 1, "The docstring becomes the description the model reads."))

sim("createagent", "m1", "create_agent(): the full loop, step by step",
    "This does everything from the previous lesson automatically, again and again until finished.",
    [USER, "Agent", MODEL, TOOL],
    'from langchain.agents import create_agent\n\nagent = create_agent(\n    "anthropic:claude-sonnet-5-5",\n    tools=[get_weather],\n    system_prompt="Be brief.",\n)\n\nresult = agent.invoke(\n    {"messages": [{"role": "user", "content": "Weather in Paris?"}]}\n)\nprint(result["messages"][-1].content)',
    [st("Build the agent", "This creates a small LangGraph graph with two main steps: call the model, and run tools.", l=(3, 7), s={"agent": "graph: model <-> tools"}),
     st("Start with one message", "The agent keeps its working memory in `state`. `messages` is the main item.", (USER, "Agent", "Weather in Paris?"), l=(9, 11), s={"state.messages": ["human: Weather in Paris?"]}),
     st("Loop 1: model step", "The system prompt, messages and tool descriptions go to the model.", ("Agent", MODEL, "request"), l=9),
     st("Loop 1: model asks for a tool", "The answer has a tool request, so the agent knows it isn't finished.", (MODEL, "Agent", "tool call"), l=9, s={"state.messages": ["human: Weather in Paris?", "ai: call get_weather(Paris)"]}),
     st("Loop 1: tools step", "The agent runs the requested function for you.", ("Agent", TOOL, "city=Paris"), l=9),
     st("Loop 1: result saved", "The result is added to the messages.", (TOOL, "Agent", "Sunny in Paris"), l=9, s={"state.messages": ["human: Weather in Paris?", "ai: call get_weather(Paris)", "tool: Sunny in Paris"]}),
     st("Loop 2: model step", "All three messages go back to the model.", ("Agent", MODEL, "3 messages"), l=9),
     st("Loop 2: final answer", "No tool request this time, so the loop stops.", (MODEL, "Agent", "It is sunny."), l=9, s={"state.messages": ["human: Weather in Paris?", "ai: call get_weather(Paris)", "tool: Sunny in Paris", "ai: It is sunny in Paris."]}),
     st("You get the whole state", "`result` contains every message. `[-1]` means the last one, which is the final answer.", ("Agent", USER, "result"), l=12)],
    ("What tells the agent to stop looping?", ["A fixed count of 2", "The model's reply has no tool requests", "The tool returns True"], 1, "When the model replies with no tool request, the loop ends."))

sim("structured", "m1", "Structured output: forcing a fixed shape",
    "Use this when your program, not a person, needs to read the answer.",
    [PY, LC, MODEL],
    'from pydantic import BaseModel, Field\n\nclass Movie(BaseModel):\n    title: str = Field(description="Movie title")\n    year: int\n\nstructured = model.with_structured_output(Movie)\nmovie = structured.invoke("Tell me about Inception")\n\nprint(movie.year + 1)',
    [st("Describe the shape", "This class says the result must have a text `title` and a whole-number `year`.", l=(3, 5), s={"Movie": {"title": "str", "year": "int"}}),
     st("Attach the shape", "This makes a new runnable that returns a `Movie`, instead of plain text.", l=7),
     st("The shape is sent with the question", "The shape travels with the request, so the model knows the required fields.", (LC, MODEL, "question + shape"), l=8),
     st("The model fills in the fields", "The model returns data matching the shape.", (MODEL, LC, '{"title":"Inception","year":2010}'), l=8),
     st("Python checks it", "Pydantic checks the data. If `year` were the word “soon”, you'd get an error rather than bad data in your program.", (LC, PY, "Movie object"), l=8, s={"movie.title": "Inception", "movie.year": 2010}),
     st("Use it like normal data", "`year` is a real number, so maths works without any text parsing.", l=10, s={"printed": 2011})],
    ("When is structured output most useful?", ["When code needs to read the result", "When writing a poem", "When you want a slower model"], 0, "It gives your code predictable fields."))

sim("streaming", "m1", "Streaming: why text appears word by word",
    "The same answer, delivered in pieces.",
    [USER, PY, MODEL],
    'for chunk in model.stream("Explain APIs briefly"):\n    print(chunk.content, end="")',
    [st("Ask for a stream", "`stream` opens the connection and gives you pieces as they are made.", (PY, MODEL, "stream request"), l=1),
     st("First piece", "A small piece arrives long before the full answer exists.", (MODEL, PY, "An"), l=1, s={"chunk.content": "An", "screen": "An"}),
     st("Shown immediately", "The loop body prints it at once.", (PY, USER, "An"), l=2),
     st("Next piece", "The loop goes back to the top and waits for the next piece.", (MODEL, PY, " API"), l=1, s={"chunk.content": " API", "screen": "An API"}),
     st("And again", "This keeps going.", (MODEL, PY, " connects"), l=1, s={"chunk.content": " connects", "screen": "An API connects"}),
     st("The stream ends", "The provider signals the end and the `for` loop finishes. The total time is about the same, but it feels much faster.", (MODEL, PY, "end"), l=1, s={"screen": "An API connects programs."})])

sim("middleware", "m1", "Middleware: code that runs around each step",
    "Middleware lets you check or change what goes in and out of the model, without rewriting the agent.",
    ["Agent", "Middleware", MODEL],
    'from langchain.agents import create_agent\nfrom langchain.agents.middleware import before_model, after_model\n\n@before_model\ndef log_count(state, runtime):\n    print("sending", len(state["messages"]), "messages")\n\n@after_model\ndef check(state, runtime):\n    print("model replied")\n\nagent = create_agent("anthropic:claude-sonnet-5-5", tools=[], middleware=[log_count, check])',
    [st("Register the hooks", "You pass your functions in the `middleware` list.", l=11, s={"middleware": ["log_count", "check"]}),
     st("A model step begins", "Before calling the model, the agent runs every “before” hook.", ("Agent", "Middleware", "state"), l=(4, 6), s={"printed": "sending 1 messages"}),
     st("A hook can change things", "A hook can return updates to the state, or jump to the end to stop the run. This is how limits and safety checks are built.", ("Middleware", "Middleware")),
     st("The model is called", "If nothing stopped it, the request goes out.", ("Middleware", MODEL, "request")),
     st("The answer returns", "The answer comes back.", (MODEL, "Middleware", "AI message")),
     st("The after hook runs", "Now the “after” hook can inspect or change the answer.", ("Middleware", "Middleware"), l=(8, 10), s={"printed": "model replied"}),
     st("The agent continues", "Control returns to the normal loop.", ("Middleware", "Agent", "updated state"))],
    ("What is middleware good for?", ["Limits, logging and safety checks around model calls", "Replacing Python", "Installing packages"], 0, "It wraps steps so you can add behaviour around them."))

# ---------- Module 2 ----------
sim("graph", "m2", "A LangGraph run, node by node",
    "A graph is a list of steps, connections between them, and one shared notebook called state.",
    ["START", "write", "polish", "END"],
    'from typing import TypedDict\nfrom langgraph.graph import StateGraph, START, END\n\nclass State(TypedDict):\n    draft: str\n\ndef write(state):\n    return {"draft": "hello world"}\n\ndef polish(state):\n    return {"draft": state["draft"].title()}\n\nbuilder = StateGraph(State)\nbuilder.add_node("write", write)\nbuilder.add_node("polish", polish)\nbuilder.add_edge(START, "write")\nbuilder.add_edge("write", "polish")\nbuilder.add_edge("polish", END)\n\ngraph = builder.compile()\nresult = graph.invoke({"draft": ""})',
    [st("Define the notebook", "`State` lists what the steps can read and write.", l=(4, 5)),
     st("Steps are normal functions", "Each receives the current state and returns only what it wants to change.", l=(7, 11)),
     st("Draw the map", "These lines register the steps and the arrows between them. Nothing has run.", l=(13, 18)),
     st("Compile", "`compile` checks the map for mistakes and makes it runnable.", l=20, s={"graph": "ready"}),
     st("Start", "`invoke` puts your input into state and starts at START.", ("START", "write", "state"), l=21, s={"state.draft": ""}),
     st("write runs", "The `write` function returns one change.", ("write", "write"), l=(7, 8), s={"state.draft": "hello world"}),
     st("Follow the arrow", "The edge says `polish` is next.", ("write", "polish", "state"), l=17),
     st("polish runs", "It reads the draft and returns the new value.", ("polish", "polish"), l=(10, 11), s={"state.draft": "Hello World"}),
     st("Reach END", "The edge leads to END and the run stops.", ("polish", "END", "state"), l=18),
     st("You get the final state", "`result` is the finished notebook.", l=21, s={"result": {"draft": "Hello World"}})],
    ("What should a node return?", ["The whole program", "Only the state values it wants to change", "Nothing, ever"], 1, "A node returns just the updates to apply."))

sim("conditional", "m2", "Conditional edges: the graph makes a decision",
    "A normal edge always goes to the same place. A conditional edge runs a function to choose.",
    ["START", "classify", "refund", "sales", "END"],
    'def route(state):\n    return "refund" if state["kind"] == "refund" else "sales"\n\nbuilder.add_edge(START, "classify")\nbuilder.add_conditional_edges("classify", route, ["refund", "sales"])\nbuilder.add_edge("refund", END)\nbuilder.add_edge("sales", END)',
    [st("Input arrives", "A customer writes “I want my money back.”", ("START", "classify", "message"), s={"state.text": "I want my money back"}),
     st("classify writes its verdict", "This node adds a label to the state.", ("classify", "classify"), s={"state.kind": "refund"}),
     st("The routing function runs", "`route` reads the state and returns the name of the next node. It does not change the state.", ("classify", "classify"), l=(1, 2), s={"route() returned": "refund"}),
     st("The graph jumps there", "The returned name decides the next step.", ("classify", "refund", "state"), l=5),
     st("refund runs", "The `sales` node never runs in this trip.", ("refund", "refund"), s={"state.reply": "Refund started."}),
     st("End", "The refund branch's edge leads to END.", ("refund", "END", "state"), l=6)],
    ("A routing function should…", ["Return the next node's name", "Delete the state", "Call every node"], 0, "It returns where to go next."))

sim("reducer", "m2", "Reducers: why messages add up instead of being replaced",
    "By default, a new value replaces the old one. A reducer changes that rule.",
    ["Node", "Reducer", "State"],
    'from typing import Annotated, TypedDict\nfrom operator import add\n\nclass State(TypedDict):\n    title: str\n    notes: Annotated[list, add]',
    [st("Two fields, two rules", "`title` has no rule, so it will be replaced. `notes` has the `add` rule, so new lists get joined on.", l=(5, 6), s={"title": "Draft", "notes": ["a"]}),
     st("A node returns updates", "A node returns a new title and a new note.", ("Node", "Reducer", '{title:"Final", notes:["b"]}')),
     st("title is replaced", "No reducer means the old value is thrown away.", ("Reducer", "State", "title"), l=5, s={"title": "Final"}),
     st("notes is combined", "The reducer computes `old + new`.", ("Reducer", "State", "notes"), l=6, s={"notes": ["a", "b"]}),
     st("Why it matters", "`MessagesState` uses a smart reducer for `messages`, so each step adds to the conversation instead of erasing it.")],
    ("Without a reducer, a returned value…", ["Replaces the old value", "Is ignored", "Is appended"], 0, "Replacement is the default rule."))

sim("checkpoint", "m2", "Checkpoints: how a graph remembers between calls",
    "A checkpointer saves the state after each step, under a thread ID.",
    [PY, "Graph", "Checkpointer"],
    'from langgraph.checkpoint.memory import InMemorySaver\n\ngraph = builder.compile(checkpointer=InMemorySaver())\nconfig = {"configurable": {"thread_id": "asha-1"}}\n\ngraph.invoke({"messages": [("user", "I am Asha")]}, config)\ngraph.invoke({"messages": [("user", "Who am I?")]}, config)',
    [st("Attach the saver", "The graph now saves after every step. `InMemorySaver` keeps it in RAM, so it is for learning and testing.", l=3),
     st("Name the conversation", "The thread ID is the label on the folder where this conversation is saved.", l=4, s={"thread_id": "asha-1"}),
     st("First call", "The graph looks for saved state under `asha-1` and finds none.", (PY, "Graph", "I am Asha"), l=6),
     st("Saved after each step", "As each step finishes, a checkpoint is written.", ("Graph", "Checkpointer", "checkpoint 1"), l=6, s={"saved[asha-1]": ["user: I am Asha", "ai: Hello Asha"]}),
     st("Second call, same ID", "You send only the new message.", (PY, "Graph", "Who am I?"), l=7),
     st("The old state is loaded", "The graph restores the saved messages.", ("Checkpointer", "Graph", "2 old messages"), l=7),
     st("The model sees all of it", "The new message is added, so the model can answer.", ("Graph", "Graph"), l=7, s={"saved[asha-1]": ["user: I am Asha", "ai: Hello Asha", "user: Who am I?", "ai: You are Asha"]}),
     st("A different ID is a different memory", "Using `thread_id: bob-1` would start empty. Threads never mix.")],
    ("What separates one conversation's memory from another?", ["The model name", "The thread ID", "The Python version"], 1, "Each thread ID has its own saved history."))

sim("interrupt", "m2", "Human approval: pausing a graph and resuming it",
    "`interrupt` stops the graph, saves everything, and waits for a person, even for days.",
    [USER, PY, "Graph", "Checkpointer"],
    'from langgraph.types import interrupt, Command\n\ndef approve(state):\n    answer = interrupt({"question": "Send this email?"})\n    return {"approved": answer == "yes"}\n\nconfig = {"configurable": {"thread_id": "t1"}}\nfirst = graph.invoke({"email": "Hi team"}, config)\nprint(first["__interrupt__"])\n\nsecond = graph.invoke(Command(resume="yes"), config)',
    [st("The run starts", "The graph needs a checkpointer for pausing to work.", (PY, "Graph", "email"), l=8, s={"state.email": "Hi team"}),
     st("The node hits interrupt", "Inside `approve`, this line stops the graph right here.", ("Graph", "Graph"), l=4),
     st("Everything is saved", "The state and the position in the graph are stored.", ("Graph", "Checkpointer", "paused at approve"), l=4, s={"saved": "paused at approve"}),
     st("Your program gets the question", "`invoke` returns, carrying the question in `__interrupt__`.", ("Graph", PY, "Send this email?"), l=9),
     st("A person decides", "No code is running. This could take five seconds or five days.", (PY, USER, "Send this email?")),
     st("You resume", "`Command(resume=...)` delivers the answer to the same thread.", (USER, "Graph", "yes"), l=11),
     st("The node runs again from its top", "Important: the node restarts from its first line, so any code before `interrupt` runs twice. This time `interrupt` returns “yes”.", ("Checkpointer", "Graph", "restore"), l=(3, 4), s={"answer": "yes"}),
     st("The graph carries on", "The node finishes and the graph continues.", ("Graph", "Graph"), l=5, s={"state.approved": True, "saved": "finished"})],
    ("When the graph resumes, the paused node…", ["Continues mid-line", "Restarts from its first line", "Is skipped"], 1, "It re-runs from the top, so put side effects after the interrupt."))

sim("streammodes", "m2", "Stream modes: choosing what you get to watch",
    "The same run, seen through different windows.",
    ["Graph", PY],
    'for chunk in graph.stream(inputs, stream_mode="updates"):\n    print(chunk)',
    [st("updates", "After each node you receive only what that node changed.", ("Graph", PY, '{"write":{"draft":"hello"}}'), l=1, s={"stream_mode": "updates"}),
     st("values", "After each step you receive the entire state.", ("Graph", PY, '{"draft":"hello"}'), s={"stream_mode": "values"}),
     st("messages", "You receive model output token by token, for chat screens.", ("Graph", PY, '("He", metadata)'), s={"stream_mode": "messages"}),
     st("custom", "You receive anything your node chooses to send, like “40% done”.", ("Graph", PY, "40% done"), s={"stream_mode": "custom"}),
     st("debug", "You receive detailed information about each step for investigation.", ("Graph", PY, "task details"), s={"stream_mode": "debug"})])

sim("subgraph", "m2", "Subgraphs: a graph inside a graph",
    "Use one when a piece of work is big enough to deserve its own map.",
    ["Parent", "Subgraph: research", "Parent end"],
    'sub = StateGraph(SubState)\n# ...add nodes...\nresearch = sub.compile()\n\nparent = StateGraph(State)\nparent.add_node("research", research)',
    [st("A compiled graph can be a node", "The compiled `research` graph is added like any function.", l=(3, 6)),
     st("Parent reaches the node", "The shared keys of the state are passed in.", ("Parent", "Subgraph: research", "state"), l=6, s={"parent.topic": "APIs"}),
     st("The inner graph runs its own steps", "It has its own private keys too.", ("Subgraph: research", "Subgraph: research"), s={"sub.notes": ["fact 1", "fact 2"]}),
     st("Results go back", "Only keys shared with the parent flow back. Private keys stay inside.", ("Subgraph: research", "Parent end", "summary"), s={"parent.summary": "APIs connect programs", "sub.notes": None})])

# ---------- Module 3 ----------
sim("deep", "m3", "A Deep Agent working on a long job",
    "A normal agent can lose its way on long jobs. A deep agent adds a plan, files and helpers.",
    [USER, "Deep agent", MODEL, "Files", "Helper"],
    'from deepagents import create_deep_agent\n\nagent = create_deep_agent(\n    model="anthropic:claude-sonnet-5-5",\n    tools=[internet_search],\n    system_prompt="You are a careful researcher.",\n)\nresult = agent.invoke({"messages": [{"role": "user", "content": "Write a report on APIs"}]})',
    [st("Create it", "You get planning, file and helper tools automatically, alongside your own.", l=(3, 7), s={"tools": ["internet_search", "write_todos", "ls", "read_file", "write_file", "edit_file", "task"]}),
     st("The job arrives", "This job is too large for one quick reply.", (USER, "Deep agent", "Write a report"), l=8),
     st("It makes a plan", "The model calls `write_todos` to record a checklist.", ("Deep agent", MODEL, "request"), s={"todos": ["[ ] Research", "[ ] Draft", "[ ] Review"]}),
     st("It hands off research", "The `task` tool starts a helper with a fresh, focused memory.", ("Deep agent", "Helper", "research APIs")),
     st("The helper works alone", "Its many searches stay in its own memory and don't fill up the main agent's.", ("Helper", "Helper"), s={"todos": ["[x] Research", "[ ] Draft", "[ ] Review"]}),
     st("Only a summary returns", "The main agent gets a short result.", ("Helper", "Deep agent", "summary")),
     st("It writes to files", "Long text goes into a file instead of the conversation.", ("Deep agent", "Files", "write_file report.md"), s={"files": {"report.md": "# APIs ..."}, "todos": ["[x] Research", "[x] Draft", "[ ] Review"]}),
     st("It finishes", "It reads the file back to review it, ticks the last item, and replies.", ("Deep agent", USER, "Report is ready"), s={"todos": ["[x] Research", "[x] Draft", "[x] Review"]})],
    ("Why use a helper for research?", ["It keeps the main agent's context small", "It is required by Python", "It makes tools free"], 0, "The noisy work stays in the helper's own context."))

sim("deepfs", "m3", "Virtual files: where a deep agent keeps its work",
    "These files are by default stored in the agent's state, not on your disk.",
    ["Agent", "Backend", "Where it lives"],
    "",
    [st("The agent writes a file", "The model calls `write_file`.", ("Agent", "Backend", "write_file notes.md")),
     st("A backend decides where it goes", "The backend is the storage choice. By default it is the agent's state, so your real disk is untouched.", ("Backend", "Where it lives", "state"), s={"state.files": {"notes.md": "..."}}),
     st("Reading it back", "`read_file` gets it through the same backend.", ("Where it lives", "Agent", "contents")),
     st("Other backends", "You can pick others: a real folder on disk, a long-term store that survives between threads, or a sandbox. Each changes the risk: a real-disk backend lets the agent change your actual files.")])

sim("deepmem", "m3", "Long-term memory across conversations",
    "Thread memory ends with the thread. A store outlives it.",
    ["Thread A", "Store", "Thread B"], "",
    [st("In thread A", "The user says they prefer short answers.", ("Thread A", "Thread A"), s={"thread_A.messages": ["I prefer short answers"]}),
     st("It is saved long-term", "The agent writes the fact to the store under a namespace, such as the user's ID.", ("Thread A", "Store", "preference"), s={"store[user-1]": {"style": "short"}}),
     st("A new thread starts", "Thread B has an empty conversation.", ("Store", "Store"), s={"thread_B.messages": []}),
     st("It reads the store", "Thread B loads the stored preference.", ("Store", "Thread B", "style=short")),
     st("The rule of thumb", "**Checkpointer** remembers this conversation. **Store** remembers across conversations.")],
    ("Which keeps a fact across different threads?", ["Checkpointer", "Store", "A longer prompt"], 1, "A store is shared across threads."))

# ---------- Module 4 ----------
sim("mdafolder", "m4", "Managed Deep Agents: the project folder, file by file",
    "Here you describe an agent as a folder. Each file switches on one feature.",
    ["Your folder", "mda build", "Running agent"], "",
    [st("agent.py (required)", "The model and core options. This is the only file that must exist.", ("Your folder", "mda build", "agent.py"), s={"found": ["agent.py"]}),
     st("instructions.md", "The agent's instructions in plain text.", s={"found": ["agent.py", "instructions.md"]}),
     st("skills/", "Reusable know-how the agent can load when needed.", s={"found": ["agent.py", "instructions.md", "skills/"]}),
     st("tools/ and tools/mcp.py", "Your own tools, and connections to MCP tool servers.", s={"found": ["agent.py", "instructions.md", "skills/", "tools/", "tools/mcp.py"]}),
     st("middleware/", "Your own code that runs around steps."),
     st("sandbox/", "Where the agent's code can run safely."),
     st("memory.py and identity.py", "How the agent remembers things, and how it knows who is calling."),
     st("channels/ and schedules/", "How people reach it, such as Slack, and when it runs on a timer."),
     st("evals/", "Tests for your agent."),
     st("The folder is compiled", "`mda build` turns all of it into a runnable app.", ("mda build", "Running agent", "compiled app"), s={"build": ".mda/build"})],
    ("Which file is required?", ["instructions.md", "agent.py", "evals/"], 1, "agent.py is the required file."), beta=True)

sim("mdaflow", "m4", "From mda init to mda deploy",
    "The commands you would type, and what each does.",
    [USER, "mda", "Local server", "LangSmith"],
    "mda init research-assistant\ncd research-assistant\nuv sync\nmda dev\nmda deploy",
    [st("mda init", "Creates a starter folder with `agent.py`, `instructions.md`, `identity.py`, a `sandbox/` and `.env`.", (USER, "mda", "init"), l=1, s={"folder": "research-assistant"}),
     st("uv sync", "Installs the Python packages the project needs.", l=3),
     st("Keys go in .env", "`mda dev` reads your API keys from this file. Keep it private."),
     st("mda dev", "Compiles the project and starts a local Agent Server.", ("mda", "Local server", "compiled app"), l=4, s={"running": "local"}),
     st("Try it locally", "You chat with it through `mda chat` or Studio, at no hosting cost.", (USER, "Local server", "hello")),
     st("mda deploy", "Sends the project to LangSmith, which runs it for you. Needs a paid plan, so here it is simulated.", ("mda", "LangSmith", "project"), l=5, s={"running": "LangSmith Cloud (simulated)"})],
    lang="text", beta=True)

# ---------- Module 5 ----------
sim("server", "m5", "Agent Server: assistants, threads and runs",
    "Agent Server turns your graph into a web service. Three words explain it.",
    ["Your app", "Agent Server", "Graph", "Database"],
    'POST /threads\n{}\n\nPOST /threads/{thread_id}/runs/wait\n{"assistant_id": "agent",\n "input": {"messages": [{"role": "user", "content": "hi"}]}}',
    [st("The assistant", "An assistant is your graph plus a saved configuration. `langgraph dev` creates one automatically, named after the graph.", s={"assistant": "agent"}),
     st("Make a thread", "A thread is a container for one conversation.", ("Your app", "Agent Server", "POST /threads"), l=1),
     st("You get its ID", "Save this ID to continue the conversation later.", ("Agent Server", "Your app", "thread_id"), s={"thread_id": "a1b2-..."}),
     st("Start a run", "A run is one execution of an assistant on a thread.", ("Your app", "Agent Server", "POST .../runs/wait"), l=(4, 6)),
     st("The server loads history", "Earlier state for this thread is loaded.", ("Database", "Agent Server", "saved state")),
     st("The graph runs", "This is the same graph you wrote in Python.", ("Agent Server", "Graph", "input")),
     st("Progress is saved", "Checkpoints are written for you automatically.", ("Graph", "Database", "checkpoint"), s={"run.status": "running"}),
     st("The result returns", "`/runs/wait` waits until the run finishes. Other routes stream or run in the background.", ("Agent Server", "Your app", "final state"), s={"run.status": "success"})],
    ("A run is…", ["A saved configuration", "One execution on a thread", "A conversation container"], 1, "A run is one execution."), lang="text")

sim("devserver", "m5", "langgraph dev and Studio",
    "Your agent runs on your PC, and Studio is a web page that connects to it.",
    [USER, "langgraph dev", "Studio page", "Your graph"],
    '{\n  "dependencies": ["."],\n  "graphs": { "agent": "./agent.py:agent" },\n  "env": ".env"\n}',
    [st("langgraph.json", "This tells the server where your graph lives: file `agent.py`, variable `agent`.", l=3),
     st("Start the server", "`langgraph dev` runs on your PC at `http://127.0.0.1:2024`. It needs no Docker or database.", (USER, "langgraph dev", "start"), s={"server": "127.0.0.1:2024"}),
     st("The page connects", "Studio is hosted by LangSmith, but it connects to your local server.", ("Studio page", "langgraph dev", "connect")),
     st("You send input", "You type a message into Studio.", (USER, "Studio page", "hi")),
     st("The graph runs on your PC", "The server runs your code.", ("langgraph dev", "Your graph", "input")),
     st("You see each node", "Studio draws the graph and shows the state at every step.", ("Your graph", "Studio page", "node updates")),
     st("Edit and retry", "You can edit past state and re-run from that point, which is the fastest way of debugging.")], lang="json")

# ---------- Module 6 ----------
sim("trace", "m6", "How a trace gets built",
    "A trace is a tree of runs that records everything that happened in one request.",
    [PY, "SDK queue", "LangSmith"],
    'import os\nos.environ["LANGSMITH_TRACING"] = "true"\nos.environ["LANGSMITH_API_KEY"] = "lsv2_..."\n\nfrom langsmith import traceable\n\n@traceable\ndef answer(question):\n    return model.invoke(question).content\n\nanswer("What is an API?")',
    [st("Switch tracing on", "Two settings are enough. LangChain and LangGraph then record themselves automatically.", l=(2, 3), s={"tracing": True}),
     st("Mark your own function", "`@traceable` records your own function too.", l=(7, 9)),
     st("The top run starts", "A trace begins with its first run.", (PY, "SDK queue", "start: answer"), l=11, s={"trace": ["answer (running)"]}),
     st("A child run starts", "The model call becomes a run inside `answer`.", (PY, "SDK queue", "start: model"), l=9, s={"trace": ["answer (running)", "  model (running)"]}),
     st("The child finishes", "Inputs, outputs, tokens and time are recorded.", (PY, "SDK queue", "end: model"), l=9, s={"trace": ["answer (running)", "  model 820ms, 23 tokens"]}),
     st("The top run finishes", "The tree is now complete.", (PY, "SDK queue", "end: answer"), s={"trace": ["answer 830ms", "  model 820ms, 23 tokens"]}),
     st("Sent in the background", "The queue uploads in batches, so your program isn't slowed down.", ("SDK queue", "LangSmith", "batch")),
     st("How it counts toward the free plan", "One whole tree counts as **one trace**: the free plan allows 5,000 a month with no card on file. Each run create or update counts as an **event**, with a limit of 50,000 an hour.", s={"traces_this_month": 1, "events_this_hour": 4})],
    ("Two model calls inside one request count as…", ["Two traces", "One trace with several runs", "Zero traces"], 1, "One request makes one trace, with a run for each step."))

sim("monitor", "m6", "From traces to dashboards, alerts and automations",
    "Once traces arrive, LangSmith can act on them.",
    ["Traces", "Rule", "Alert", "Queue", "You"], "",
    [st("A trace arrives", "It carries its agent and environment.", ("Traces", "Rule", "trace"), s={"trace": {"agent": "checkout", "env": "production", "error": True}}),
     st("Dashboards count it", "Each environment has its own charts for volume, latency, errors and cost."),
     st("An automation rule filters it", "A rule says: if this matches, do something, such as adding it to a dataset or review queue.", ("Rule", "Queue", "matched trace"), s={"queue": 1}),
     st("Billing warning", "Rules that extend retention upgrade the whole trace to longer storage, which costs more on paid plans."),
     st("An alert watches the rate", "If errors in production go above your limit, you are notified. Local runs stay quiet.", ("Alert", "You", "Errors above 5%")),
     st("A person leaves feedback", "Scores and notes attach to the trace, and become future test data.", ("You", "Traces", "score 0"), s={"trace.feedback": 0})])

# ---------- Module 7 ----------
sim("offline", "m7", "An offline experiment, example by example",
    "Offline evaluation tests one version of your agent against a saved list, before you release it.",
    ["Dataset", "Your agent", "Evaluator", "Experiment"],
    'from langsmith import Client\n\nclient = Client()\n\ndef correct(outputs, reference_outputs):\n    return outputs["answer"] == reference_outputs["answer"]\n\nresults = client.evaluate(\n    my_agent,\n    data="capitals",\n    evaluators=[correct],\n    experiment_prefix="v2",\n)',
    [st("The dataset is the test paper", "Each example has an input and the expected output.", s={"dataset.capitals": [{"in": "France?", "want": "Paris"}, {"in": "Japan?", "want": "Tokyo"}]}),
     st("An evaluator is the marker", "Here it is plain code. It could also be a person, an LLM judge or a side-by-side comparison.", l=(5, 6)),
     st("Example 1 goes in", "`evaluate` runs your agent.", ("Dataset", "Your agent", "France?"), l=8),
     st("The agent answers", "Its output goes to the marker.", ("Your agent", "Evaluator", "Paris")),
     st("It is marked", "The score is saved.", ("Evaluator", "Experiment", "correct=1"), s={"scores": [1]}),
     st("Example 2", "The next example runs.", ("Dataset", "Your agent", "Japan?")),
     st("A wrong answer", "The agent says Kyoto, so it scores 0.", ("Evaluator", "Experiment", "correct=0"), s={"scores": [1, 0]}),
     st("Compare versions", "`v2` averages 50%. If `v1` had 100%, you've found a regression before users did.", s={"summary": {"v2": "50%", "v1": "100%"}})],
    ("Offline evaluation runs…", ["On saved examples before release", "Only on live users", "Only in the browser"], 0, "Offline uses a dataset, before you ship."))

sim("online", "m7", "Online evaluation on live traffic",
    "Online evaluators score real requests, where there is no correct answer to compare to.",
    ["User", "Agent", "Sampler", "Evaluator", "Dataset"], "",
    [st("A real request is traced", "A trace arrives in production.", ("User", "Agent", "question")),
     st("A sample is chosen", "Scoring everything costs money, so you set a sampling rate such as 10%.", ("Agent", "Sampler", "trace"), s={"sampling_rate": "10%"}),
     st("It gets scored", "With no reference answer, it checks things like safety, format or helpfulness.", ("Sampler", "Evaluator", "trace"), s={"score.helpful": 0}),
     st("Retention warning", "New online evaluators extend retention by default, which costs more on paid plans."),
     st("Close the loop", "Failing traces are added to the dataset. You fix the agent, confirm the fix offline, and release.", ("Evaluator", "Dataset", "failing example"), s={"dataset_size": 21})])

# ---------- Module 8 ----------
sim("hosting", "m8", "Four ways to host: who runs what",
    "All four use the same Agent Server. The difference is who operates each part.",
    ["You", "Control plane", "Data plane", "LangChain"], "",
    [st("Two halves", "The **control plane** manages deployments. The **data plane** runs your Agent Servers and databases."),
     st("Cloud", "LangChain runs both halves. You connect GitHub or run `langgraph deploy`. Needs Plus or above.", ("LangChain", "Control plane", "runs both"), s={"control": "LangChain", "data": "LangChain"}),
     st("Hybrid", "LangChain runs the control plane. Your Agent Servers run in your infrastructure.", ("You", "Data plane", "runs agents"), s={"control": "LangChain", "data": "You"}),
     st("Self-hosted with control plane", "You run both in your own Kubernetes. Enterprise only. Used for full data residency.", ("You", "Control plane", "runs both"), s={"control": "You", "data": "You"}),
     st("Standalone server", "Just Agent Server containers with your own PostgreSQL and Redis, and no control plane.", ("You", "Data plane", "containers"), s={"control": "None", "data": "You"})],
    ("In Hybrid, who runs the Agent Servers?", ["LangChain", "You", "Nobody"], 1, "Hybrid keeps Agent Servers and data in your infrastructure."))

sim("deployflow", "m8", "A deployment going live",
    "What happens after you press deploy. This is a simulation: hosted deployment needs a paid plan.",
    ["You", "GitHub", "Control plane", "Builder", "Agent Server"], "",
    [st("You choose a repo", "You connect GitHub and select the repository and branch.", ("You", "GitHub", "connect")),
     st("The control plane pulls it", "It reads your `langgraph.json`.", ("GitHub", "Control plane", "code")),
     st("An image is built", "Your code and packages become a container.", ("Control plane", "Builder", "build"), s={"revision": "building"}),
     st("The server starts", "A new Agent Server starts with a database behind it.", ("Builder", "Agent Server", "image"), s={"revision": "deploying"}),
     st("Live", "You get a URL and call it with your LangSmith API key.", ("Agent Server", "You", "URL"), s={"revision": "live"}),
     st("You push new code", "A new revision is built. Billing is based on the compute and database each deployment requests.", ("GitHub", "Control plane", "new commit"), s={"revision": "building r2"})])

# ---------- Module 9 ----------
sim("registry", "m9", "Agent Registry: how a trace finds its agent",
    "The registry lists every agent in one place, and each trace lands under one agent and one environment.",
    ["Your code", "LangSmith", "checkout agent", "production"],
    'LANGSMITH_AGENT=checkout\nLANGSMITH_ENVIRONMENT=production',
    [st("Register the agent", "You create it once. Its **identifier** cannot change. Its **display name** can.", s={"identifier": "checkout", "display_name": "Checkout Helper"}),
     st("Your code says where to send traces", "The identifier and environment travel with each trace.", ("Your code", "LangSmith", "trace"), l=(1, 2)),
     st("LangSmith finds the agent", "It finds the agent by identifier, not display name.", ("LangSmith", "checkout agent", "route")),
     st("It lands in one environment", "The names are fixed: Production, Staging, Development and Local.", ("checkout agent", "production", "trace"), s={"environment": "production"}),
     st("You rename the agent", "Only the label changes. Old traces stay, and new ones arrive in the same place.", s={"display_name": "Checkout Bot"}),
     st("What is attached", "Alerts, evaluators and prebuilt dashboards belong to one environment of one agent. A dataset attaches to agents, and to no environment.")],
    ("What must stay stable for traces to route?", ["The display name", "The identifier", "The dashboard"], 1, "The identifier addresses traces."), lang="text")

# ---------- Module 10 ----------
sim("gateway", "m10", "LLM Gateway: one door to every model",
    "Instead of each app holding provider keys, requests go through one LangSmith endpoint.",
    ["Your app", "Gateway", "Policies", "Provider", "Trace"], "",
    [st("Your app sends a request", "It uses a LangSmith API key, not a provider key.", ("Your app", "Gateway", "model + prompt")),
     st("The gateway reads the model ID", "The ID says which provider to use.", ("Gateway", "Gateway"), s={"provider": "anthropic"}),
     st("Policies are checked", "Spend limits, rate limits and data policies apply.", ("Gateway", "Policies", "check"), s={"policy": "pass"}),
     st("The provider is called", "LangSmith holds the provider credential.", ("Gateway", "Provider", "request")),
     st("A failure, then a fallback", "If that provider fails, a fallback model can be tried.", ("Provider", "Gateway", "error 503"), s={"attempts": ["anthropic: failed"]}),
     st("The second attempt", "The fallback answers.", ("Gateway", "Provider", "fallback"), s={"attempts": ["anthropic: failed", "fallback: ok"]}),
     st("Everything is traced", "The trace shows each attempt and policy check.", ("Gateway", "Trace", "attempts + checks")),
     st("The answer returns", "If formats differ, the gateway translates. On the free plan this is pay-as-you-go by card, so it's simulated here.", ("Gateway", "Your app", "answer"))], beta=True)

sim("fleet", "m10", "Fleet: agents without code",
    "You describe an agent in the LangSmith web interface and it runs there.",
    ["You", "Fleet", "Agent", "Allowance"], "",
    [st("You describe the job", "You write what the agent should do, without code.", ("You", "Fleet", "description")),
     st("A run starts", "Fleet runs the agent.", ("Fleet", "Agent", "run")),
     st("Usage is measured", "Fleet is metered in LSUs, where 1 LSU is $1. The amount depends on the work and the model tier.", ("Agent", "Allowance", "usage"), s={"LSU_used": 1.5, "LSU_included": 7}),
     st("The allowance runs out", "The free plan includes 7 LSU a month. After that, Fleet pauses new runs until it resets or you upgrade.", ("Allowance", "Fleet", "paused"), s={"LSU_used": 7, "fleet": "paused"})])

sim("engine", "m10", "Engine: finding what keeps going wrong",
    "Engine reads your production traces and opens issues with proposed fixes.",
    ["Traces", "Engine", "Issue", "Repo", "Dataset"], "",
    [st("Engine scans", "It scans connected tracing projects on a schedule.", ("Traces", "Engine", "scan")),
     st("It groups failures", "Similar failures are clustered and ranked by severity.", ("Engine", "Issue", "new issue"), s={"issue": "Wrong refund amount", "traces": 14}),
     st("It diagnoses", "The issue shows a root cause and the traces that support it."),
     st("It proposes a fix", "It can open a pull request for agents built with Deep Agents, LangChain or LangGraph.", ("Issue", "Repo", "pull request")),
     st("It creates test examples", "Examples from those traces go in a dataset, so you can verify the fix.", ("Issue", "Dataset", "examples"), s={"dataset_added": 14}),
     st("It keeps the issue current", "New traces with the same failure get attached. **Insights** tells you how people use your agent. **Engine** tells you what's wrong.", s={"traces": 19})])

sim("dcode", "m10", "dcode: a coding agent in your terminal",
    "dcode is an open-source coding agent built on the Deep Agents SDK.",
    ["You", "dcode", "Model", "Your files", "Shell"], "dcode\n> fix the failing test\n/model\n> ",
    [st("Start it", "You run `dcode` in a project folder. It needs Python 3.14 and is installed here in its own environment.", ("You", "dcode", "start"), l=1),
     st("Give a task", "You describe what you want.", ("You", "dcode", "fix the failing test"), l=2),
     st("It reads your code", "The model asks to read files.", ("dcode", "Your files", "read"), s={"read": ["tests/test_app.py"]}),
     st("It wants to run something", "You approve shell commands from the terminal before they run.", ("dcode", "You", "Run pytest?"), s={"waiting": "your approval"}),
     st("It runs and edits", "After you approve, it runs and fixes the code.", ("dcode", "Shell", "pytest"), s={"waiting": None}),
     st("Switch models mid-session", "`/model` changes model or provider without losing your place.", ("You", "dcode", "/model"), l=3)], lang="text")

# ---------- Module 11 ----------
sim("rbac", "m11", "Permissions: can this person do this?",
    "RBAC is Enterprise-only. On other plans every user is an Admin, so it is simulated here.",
    ["User", "LangSmith", "Role check", "Audit log"], "",
    [st("A user clicks delete", "Ravi tries to delete a dataset.", ("User", "LangSmith", "delete dataset"), s={"user": "Ravi", "role": "Viewer"}),
     st("LangSmith finds the role", "Roles apply at organization and workspace level.", ("LangSmith", "Role check", "Viewer?")),
     st("The role lacks the permission", "A Viewer can read but not delete.", ("Role check", "LangSmith", "denied"), s={"decision": "403 Forbidden"}),
     st("The attempt can be recorded", "Audit logs give the organization a record of important actions.", ("LangSmith", "Audit log", "entry")),
     st("ABAC adds labels", "With attribute-based rules, access can depend on tags, such as team=finance.", s={"tag": "team=finance"})])

sim("sso", "m11", "Single sign-on: one company login",
    "The company's login system vouches for the user.",
    ["User", "LangSmith", "Company login"], "",
    [st("The user visits", "They choose to sign in with the company.", ("User", "LangSmith", "sign in")),
     st("Sent to the company", "LangSmith redirects them.", ("LangSmith", "Company login", "who is this?")),
     st("They log in there", "LangSmith never sees the password.", ("User", "Company login", "password + MFA")),
     st("The company vouches", "A signed message confirms who they are.", ("Company login", "LangSmith", "signed identity"), s={"email": "ravi@company.com"}),
     st("A session starts", "They are in, with the access set for them.", ("LangSmith", "User", "session"), s={"logged_in": True})])

sim("org", "m11", "Organization, workspace, keys and BYOC",
    "How the account parts fit together.",
    ["Organization", "Workspace", "Agent", "API key"], "",
    [st("Organization", "The top level: billing, members and overall settings.", ("Organization", "Workspace", "contains")),
     st("Workspace", "A separate area. Agents and data in one workspace stay apart from another.", ("Workspace", "Agent", "contains")),
     st("API keys", "A key lets a program act on your behalf. Keep it out of code and out of chat.", ("API key", "Workspace", "belongs to")),
     st("BYOC", "Bring Your Own Cloud runs inside your cloud account, managed by the provider."),
     st("Where the free plan fits", "One seat, up to 5,000 traces a month, and no card needed. Adding a card removes the monthly cap and allows charges.", s={"plan": "Developer", "seats": 1, "traces": 5000})])

# ---------- Module 12 ----------
sim("capstone", "m12", "Capstone: one agent's whole life",
    "Everything you've learned, in one journey.",
    ["Build", "Trace", "Test", "Deploy", "Monitor"], "",
    [st("Build", "You write a support agent with `create_agent` and two tools.", ("Build", "Build"), s={"version": "v1"}),
     st("Run locally", "`langgraph dev` serves it and Studio shows each step.", ("Build", "Trace", "local run")),
     st("Trace", "Traces show that it calls the wrong tool for refunds.", ("Trace", "Trace"), s={"bug": "wrong tool"}),
     st("Save the failure", "You add that trace to a dataset, so a failure seen once becomes a test.", ("Trace", "Test", "example"), s={"dataset": 1}),
     st("Fix and test", "You improve the tool's description and run an experiment. It passes.", ("Test", "Test"), s={"version": "v2", "score": "100%", "bug": None}),
     st("Deploy", "The new revision goes live, with a thread for each customer.", ("Test", "Deploy", "v2"), s={"live": "v2"}),
     st("Monitor", "An alert watches errors, and an online evaluator samples live answers.", ("Deploy", "Monitor", "traces")),
     st("The loop starts again", "A new failure appears, joins the dataset, and the cycle continues. That cycle **is** agent engineering.", ("Monitor", "Build", "new failing trace"), s={"dataset": 2})],
    ("What turns a one-time failure into a permanent test?", ["Adding its trace to a dataset", "Restarting the server", "Changing the display name"], 0, "A dataset example keeps checking that failure forever."))
