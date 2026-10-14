"""Existing retry utility: reuse requires checking operation idempotency."""
import time


def retry_call(operation, attempts=3, delay=0.1):
    for attempt in range(attempts):
        try:
            return operation()
        except TimeoutError:
            if attempt + 1 == attempts:
                raise
            time.sleep(delay)
