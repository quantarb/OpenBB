"""Optional durable request journal hooks; only sanitized identities cross the boundary."""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
import re
from threading import Lock
from urllib.parse import parse_qsl,urlsplit

_lock=Lock()
_active=None
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
    global _active
    with _lock:
        if _active is not None:raise RuntimeError('A request journal is already installed')
        _active=(frozenset(hosts),journal)
    try:yield
    finally:
        with _lock:_active=None


def journal_for(url):
    state=_active
    return state[1] if state and urlsplit(url).hostname in state[0] else None
