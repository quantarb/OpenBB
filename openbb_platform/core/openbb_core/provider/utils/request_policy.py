"""Optional process-scoped request admission; never receives URLs or credentials."""

from contextlib import contextmanager
from threading import Lock
from urllib.parse import urlsplit

_lock = Lock()
_policy = None


@contextmanager
def request_policy(hosts, before, after):
    """Install one policy across async worker threads, restoring on exit.

    ``after(status, retry_after)`` receives HTTP metadata before provider parsing.
    Status 0 records a transport/parsing failure; bulk consumers must not mistake
    partially successful pages for complete coverage. Callbacks receive no URLs.
    """
    global _policy
    with _lock:
        if _policy is not None:
            raise RuntimeError("A request policy is already installed")
        _policy = (frozenset(hosts), before, after)
    try:
        yield
    finally:
        with _lock:
            _policy = None


def policy_for(url):
    policy = _policy
    return policy[1:] if policy and urlsplit(url).hostname in policy[0] else None
