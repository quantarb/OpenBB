"""Optional process-scoped request admission; never receives URLs or credentials."""

from contextlib import contextmanager
from threading import Lock
from contextvars import ContextVar
from urllib.parse import urlsplit

_lock = Lock()
_policy = ContextVar('openbb_request_policy',default=None)
_required_hosts = {}


@contextmanager
def request_policy(hosts,before,after,on_response=None):
    """Context-local admission, propagated through AnyIO and asyncio tasks."""
    if _policy.get() is not None:raise RuntimeError('A request policy is already installed in this context')
    hosts=frozenset(hosts)
    with _lock:
        for host in hosts:_required_hosts[host]=_required_hosts.get(host,0)+1
    token=_policy.set((hosts,before,after,on_response))
    try:yield
    finally:
        _policy.reset(token)
        with _lock:
            for host in hosts:
                _required_hosts[host]-=1
                if not _required_hosts[host]:del _required_hosts[host]


def policy_for(url):
    policy=_policy.get();host=urlsplit(url).hostname
    if policy and host in policy[0]:return policy[1:]
    with _lock:
        if host in _required_hosts:raise RuntimeError('Request lost its required policy context; HTTP is blocked')
    return None
