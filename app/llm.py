import os

from anthropic import Anthropic
from dotenv import load_dotenv

# Load variables from a local .env file if present.
# This is optional but convenient during development.
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY environment variable is not set.\n"
        "Create a .env file or export it in your shell, e.g.\n"
        "export ANTHROPIC_API_KEY='sk-...'."
    )


def get_client() -> Anthropic:
    """Instantiate and return a singleton Anthropic client."""
    return Anthropic(api_key=API_KEY)


# Simple helper for text-completion–style calls --------------------------------


def chat(
    messages: list,
    model: str = "claude-3-haiku-20240307",  # adjust to your plan
    temperature: float = 0.7,
    max_tokens: int = 1024,
    **kwargs,
):
    """Send a chat completion request and return the response object.

    Parameters
    ----------
    messages : list[dict[str, str]]
        Conversation so far, e.g. [{"role": "user", "content": "Hello"}].
    model : str, optional
        Model name to use.
    temperature : float, optional
    max_tokens : int, optional

    Returns
    -------
    anthropic.types.Message
    """
    client = get_client()
    return client.messages.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
