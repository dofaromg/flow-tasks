"""Long timeline acceptance; synthetic cards, not model-generated film."""
import json
import os
import time
from pathlib import Path
import pytest
from MRL_Video.model import validate, VideoError
from MRL_Video.render import render, Runner, Cancelled
from MRL_Video.service import Service

FONT = Path(os.environ.get('MRL_VIDEO_TEST_FONT', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))

def plan(count=60):
    return validate(dict(schema='MRL_Video_Request/v1',title='Longfilm fixture',
        sources=[dict(id='s',original_name='synthetic',locator='test fixture',text='Test scene.')],
        scenes=[dict(title='Test',caption='Test scene.',source_id='s',duration=20,layout='quote') for _ in range(count)],
        longfilm=True,music=False,encoding=dict(width=320,height=320,crf=28,preset='ultrafast')))

def test_limits_and_frame_alignment():
    p=plan()
    assert sum(s['duration'] for s in p['scenes'])==1200
    assert validate(p)==p
    p['scenes'].append(p['scenes'][0])
    with pytest.raises(VideoError): validate(p)
    p=plan(2);p['scenes'][0]['duration']=19.999
    with pytest.raises(VideoError): validate(p)
    p=plan(2);p['longfilm']=False;p['scenes']*=2
    with pytest.raises(VideoError): validate(p)

@pytest.mark.skipif(os.environ.get('MRL_VIDEO_MEDIA_TEST')!='1',reason='opt-in real media')
def test_resume_and_cache_invalidation(tmp_path):
    p=plan(2)
    first=tmp_path/'first';first.mkdir()
    phases=[]
    def phase(value):
        phases.append(value)
        if value=='COMPOSE_AUDIO': raise Cancelled('simulated restart')
    with pytest.raises(Cancelled):render(p,first,FONT,tmp_path,Runner(lambda:False),phase)
    second=tmp_path/'second';second.mkdir()
    details=render(p,second,FONT,tmp_path,Runner(lambda:False),lambda x:None)
    assert details['cache_hits']==2
    p['encoding']['crf']=27
    third=tmp_path/'third';third.mkdir()
    details=render(p,third,FONT,tmp_path,Runner(lambda:False),lambda x:None)
    assert details['cache_hits']==0
    cache=tmp_path/'MRL_segment_cache'/(details['layouts'][0]['segment_key']+'.mp4');cache.write_bytes(b'corrupt')
    fourth=tmp_path/'fourth';fourth.mkdir()
    # Cache seal corruption cannot be silently accepted; final decode remains mandatory.
    details=render(p,fourth,FONT,tmp_path,Runner(lambda:False),lambda x:None)
    assert details['cache_hits']==1

@pytest.mark.skipif(os.environ.get('MRL_VIDEO_LONG_TEST')!='1',reason='explicit full 20 minute acceptance')
def test_full_20minute_delivery(tmp_path):
    service=Service(tmp_path/'versions',tmp_path,FONT)
    request=plan()
    jid=service.store.submit(request)["id"]
    assert service.store.claim()==jid
    started=time.monotonic();service.process(jid)
    job=service.store.get(jid)
    assert job['state']=='SUCCEEDED',job
    root=service.store.root/jid
    audit=json.loads((root/'MRL_audit.json').read_text())
    assert abs(audit['duration_seconds']-1200)<.1
    assert audit['frame_count']==28800
    result={'origin_signature':'MrLiouWord','fixture':'synthetic source-backed cards; no generative model',
            'wall_seconds':time.monotonic()-started,'audit':audit,
            'render':json.loads((root/'layout.json').read_text()),'job':jid}
    Path(os.environ.get('MRL_VIDEO_BENCHMARK','/tmp/MRL_longfilm_benchmark.json')).write_text(json.dumps(result,indent=2))
