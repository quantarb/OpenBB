import asyncio,json
import pytest
from openbb_core.provider.utils.request_journal import request_identity,safe_error,request_journal
from openbb_core.provider.utils import helpers
from test_request_policy import Session


def test_identity_is_generic_stable_and_credential_free(monkeypatch):
    a=request_identity('https://financialmodelingprep.com/stable/treasury-rates?to=2026-10-21&apikey=SECRET&from=2026-10-20')
    b=request_identity('https://financialmodelingprep.com/stable/treasury-rates?from=2026-10-20&to=2026-10-21&apikey=ROTATED')
    assert a==b and 'symbol' not in json.dumps(a) and 'SECRET' not in json.dumps(a)
    assert request_identity('https://financialmodelingprep.com/stable/available-countries')['parameters']==[]
    monkeypatch.setenv('FMP_API_KEY','private-key-value')
    assert 'private-key-value' not in safe_error(Exception('failed private-key-value https://vendor/x?apikey=other'))
    assert 'other' not in safe_error(Exception('failed https://vendor/x?apikey=other'))


def test_journal_cache_bypasses_http_and_records_real_failure(monkeypatch):
    session=Session()
    async def factory(**kwargs):return session
    monkeypatch.setattr(helpers,'get_async_requests_session',factory)
    class Journal:
        payload=None
        def lookup(self,i):return {'payload':self.payload} if self.payload is not None else None
        def started(self,i):self.identity=i
        def succeeded(self,i,result,status):self.payload=result
        def failed(self,i,error,status):self.error=(type(error).__name__,status)
    journal=Journal();url='https://financialmodelingprep.com/stable/test?apikey=private'
    with request_journal({'financialmodelingprep.com'},journal):
        result=asyncio.run(helpers.amake_request(url,session=session))
        assert asyncio.run(helpers.amake_request(url,session=session))==result
    assert len(session.calls)==1
    journal.payload=None
    async def failed(*args):raise ValueError('bad schema')
    with request_journal({'financialmodelingprep.com'},journal):
        with pytest.raises(ValueError):asyncio.run(helpers.amake_request(url,session=session,response_callback=failed))
    assert journal.error==('ValueError',200)


def test_sync_requests_share_journal_and_cache(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    class Session:
        def request(self,*args,**kwargs):
            calls.append(1)
            return SimpleNamespace(status_code=200,headers={},content=b'[]',json=lambda:[{'value':1}])
    monkeypatch.setattr(helpers,'get_requests_session',lambda **kwargs:Session())
    monkeypatch.setattr(helpers,'get_python_request_settings',lambda:{})
    class Journal:
        payload=None
        def lookup(self,i):return {'payload':self.payload} if self.payload is not None else None
        def started(self,i):pass
        def succeeded(self,i,result,status):self.payload=result
        def failed(self,*args):pytest.fail('unexpected failure')
    j=Journal()
    with request_journal({'financialmodelingprep.com'},j):
        assert helpers.make_request('https://financialmodelingprep.com/stable/x?apikey=secret').json()==[{'value':1}]
        assert helpers.make_request('https://financialmodelingprep.com/stable/x?apikey=secret').json()==[{'value':1}]
    assert len(calls)==1
