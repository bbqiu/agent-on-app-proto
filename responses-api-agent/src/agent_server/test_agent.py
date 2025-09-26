from pprint import pprint

# need to import agent for our @invoke registered function to be found
from agent_server import agent  # noqa: F401
from agent_server.server import get_invoke_function

# TODO: Replace with your agent-specific input
example_input = {"input": [{"role": "user", "content": "Calculate the 15th Fibonacci number"}]}

# Get the invoke function that was registered via @invoke decorator in your agent
invoke_fn = get_invoke_function()


# Because the agent has to be reinitialized every
def test_agent():
    assert invoke_fn is not None, (
        "No function has been decorated with @invoke. Ensure you are importing agent_server.agent."
    )

    result = invoke_fn(example_input)
    pprint(result.model_dump(exclude_none=True))
