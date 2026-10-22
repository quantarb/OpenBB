"""FMP request-level admission including individual pagination requests."""

from contextlib import contextmanager


@contextmanager
def use_request_policy(before, after, on_response=None):
    """Callbacks accept no URL; after receives HTTP status and Retry-After only."""
    from openbb_core.provider.utils.request_policy import request_policy

    with request_policy({"financialmodelingprep.com", "www.financialmodelingprep.com"}, before, after, on_response):
        yield
