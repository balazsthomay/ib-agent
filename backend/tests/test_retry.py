"""Tests for retry utility."""

import asyncio

import pytest

from app.utils.retry import RetryableHTTPError, retry_with_backoff, with_retry


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Test successful execution on first attempt."""
    call_count = 0

    async def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await retry_with_backoff(successful_func, max_retries=3)

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test successful execution after some failures."""
    call_count = 0

    async def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RetryableHTTPError("Temporary error")
        return "success"

    result = await retry_with_backoff(
        eventually_successful,
        max_retries=3,
        initial_delay=0.01,
        exceptions=(RetryableHTTPError,),
    )

    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test that all retries are exhausted and exception is raised."""
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise RetryableHTTPError("Persistent error")

    with pytest.raises(RetryableHTTPError):
        await retry_with_backoff(
            always_fails,
            max_retries=2,
            initial_delay=0.01,
            exceptions=(RetryableHTTPError,),
        )

    assert call_count == 3  # Initial attempt + 2 retries


@pytest.mark.asyncio
async def test_with_retry_decorator():
    """Test the with_retry decorator."""
    call_count = 0

    @with_retry(max_retries=2, initial_delay=0.01, exceptions=(ValueError,))
    async def decorated_func(should_fail: bool):
        nonlocal call_count
        call_count += 1
        if should_fail and call_count < 2:
            raise ValueError("Test error")
        return f"attempt_{call_count}"

    # Test success after retry
    result = await decorated_func(should_fail=True)
    assert result == "attempt_2"
    assert call_count == 2

    # Reset and test immediate success
    call_count = 0
    result = await decorated_func(should_fail=False)
    assert result == "attempt_1"
    assert call_count == 1


@pytest.mark.asyncio
async def test_exponential_backoff_timing():
    """Test that exponential backoff delay is applied correctly."""
    call_times = []

    async def failing_func():
        call_times.append(asyncio.get_event_loop().time())
        raise ValueError("Error")

    with pytest.raises(ValueError):
        await retry_with_backoff(
            failing_func,
            max_retries=2,
            initial_delay=0.1,
            exponential_base=2.0,
            exceptions=(ValueError,),
        )

    # Check that delays are approximately correct
    # First retry: ~0.1s delay
    # Second retry: ~0.2s delay
    assert len(call_times) == 3
    if len(call_times) >= 2:
        delay1 = call_times[1] - call_times[0]
        assert 0.08 < delay1 < 0.15  # Allow some tolerance
