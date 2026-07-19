from langchain_deepseek import ChatDeepSeek
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.config import settings


def get_llm(temperature: float = 0.2) -> ChatDeepSeek:
    """Return a configured DeepSeek LLM instance.

    Args:
        temperature: Sampling temperature. Use 0.0–0.2 for structured output,
                     0.3–0.5 for quiz generation, 0.7–0.8 for creative content.
    """
    return ChatDeepSeek(
        model="deepseek-chat",
        temperature=temperature,
        api_key=settings.deepseek_api_key,
    )


def invoke_llm_with_retry(chain, input_data: dict, max_attempts: int = 3):
    """Invoke a LangChain chain with exponential backoff on failure.

    Retries on any exception from DeepSeek (network errors, rate limits,
    transient server errors). Does NOT retry on OutputParserException
    (that's a prompt/schema problem, not a network problem).

    Backoff: 1s → 2s → 4s (max 3 attempts total).

    Args:
        chain: A LangChain Runnable (prompt | llm | parser chain).
        input_data: Dict of input variables for the chain.
        max_attempts: Max invocation attempts before raising. Default 3.
    """
    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _invoke():
        return chain.invoke(input_data)

    return _invoke()
