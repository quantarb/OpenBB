"""Optional durable request journal hooks; only sanitized identities cross the boundary."""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
import re
from threading import Lock
from contextvars import ContextVar
from urllib.parse import parse_qsl,urlsplit

_lock=Lock()
_active=ContextVar('openbb_request_journal',default=None)
_required_hosts={}
_SECRET=re.compile(r'(?:api[_-]?key|access[_-]?key|secret|token|password|authorization|credential|signature)',re.I)


def safe_error(error):
    text=re.sub(r'(?:https?|s3s?|gcpxmls?)://\S+','[URL]',str(error))
    text=re.sub(r'(?i)\b(api[_-]?key|secret|token|password|authorization|credential|signature)\s*[:=]\s*[\"\']?[^\s,}\"\']+',r'\1=[redacted]',text)
    for key,value in os.environ.items():
        if _SECRET.search(key) and len(value)>=8:text=text.replace(value,'[redacted]')
    return text[:600]


def request_identity(url,method='GET',params=None):
    if method.upper()!='GET':
        raise ValueError('Durable journal currently supports GET requests only; body identity required for other methods')
    parts=urlsplit(url)
    if parts.username or parts.password:
        raise ValueError('Credential-bearing request authority cannot be journaled')
    pairs=list(parse_qsl(parts.query,keep_blank_values=True))
    if params:
        extra=params.items() if isinstance(params,dict) else params
        for key,value in extra:
            for item in value if isinstance(value,(list,tuple)) else [value]:pairs.append((str(key),str(item)))
    clean=[]
    for key,value in pairs:
        if _SECRET.search(key) or key.lower()=='key':continue
        if '://' in value or _SECRET.search(value) and '=' in value:
            raise ValueError('Secret-bearing/nested URL parameter cannot be journaled')
        clean.append([key,value])
    payload=dict(operation=method.upper()+' '+(parts.hostname or '').lower()+parts.path,
                 parameters=sorted(clean))
    payload['request_id']=sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return payload


@contextmanager
def request_journal(hosts,journal):
    if _active.get() is not None:raise RuntimeError('A request journal is already installed in this context')
    hosts=frozenset(hosts)
    with _lock:
        for host in hosts:_required_hosts[host]=_required_hosts.get(host,0)+1
    token=_active.set((hosts,journal))
    try:yield
    finally:
        _active.reset(token)
        with _lock:
            for host in hosts:
                _required_hosts[host]-=1
                if not _required_hosts[host]:del _required_hosts[host]


def journal_for(url):
    host=urlsplit(url).hostname;state=_active.get()
    if state and host in state[0]:return state[1]
    with _lock:
        if host in _required_hosts:raise RuntimeError('Request lost its required journal context; HTTP is blocked')
    return None
