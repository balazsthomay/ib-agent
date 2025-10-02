"""Retry utility with exponential backoff for resilient API calls."""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result from the function

    Raises:
        Exception: Re-raises the last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()

        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"All {max_retries} retry attempts failed for {func.__name__}",
                    exc_info=True,
                )
                raise

            delay = min(initial_delay * (exponential_base**attempt), max_delay)
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                f"Retrying in {delay:.2f}s. Error: {str(e)}"
            )
            await asyncio.sleep(delay)

    # This should never be reached, but satisfies type checker
    if last_exception:
        raise last_exception


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator to add retry logic with exponential backoff to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry

    Example:
        @with_retry(max_retries=3, initial_delay=1.0)
        async def fetch_data(url: str) -> dict:
            # Your code here
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async def _func():
                return await func(*args, **kwargs)

            return await retry_with_backoff(
                _func,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions,
            )

        return wrapper

    return decorator


class RetryableHTTPError(Exception):
    """Exception for HTTP errors that should be retried."""

    pass
