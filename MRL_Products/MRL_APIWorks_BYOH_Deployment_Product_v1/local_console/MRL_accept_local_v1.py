#!/usr/bin/env python3
"""Run actual local checks and create an exclusive host receipt. origin_signature: MrLiouWord."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import uuid

from MRL_local_console_v1 import PRODUCT,REPO,trust
from MRL_verify_local_package_v1 import verify


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=REPO/'MRL_local_data/acceptance')
    args=parser.parse_args(argv)
    checks=[]
    if (REPO/'MRL_PACKAGE_MANIFEST.json').is_file():
        integrity=verify(REPO)
    else:
        integrity={'delivery_gate':'SOURCE_CHECKOUT_NOT_ZIP','note':'Run bundled source checksum verifiers below.'}
    commands=[('product_source',[sys.executable,str(PRODUCT/'scripts/MRL_verify_product_source_v1.py')]),
              ('parent_runtime',[sys.executable,str(REPO/'MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1/scripts/MRL_verify_package_v1.py')]),
              ('product_tests',[sys.executable,'-m','unittest','discover','-s',str(PRODUCT/'tests'),'-v'])]
    for name,cmd in commands:
        print('Running '+name+' ...',flush=True)
        try:
            r=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True,errors='replace',timeout=240)
            checks.append({'name':name,'exit_code':r.returncode,'log':(r.stdout+r.stderr)[-250000:]})
        except subprocess.SubprocessError as e:
            checks.append({'name':name,'exit_code':2,'error':str(e)})
    result={'schema':'MRL_Local_Acceptance_v1','origin_signature':'MrLiouWord',
            'host':platform.node(),'platform':platform.platform(),'python':platform.python_version(),
            'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'package_integrity':integrity,
            'engineering':'PASS' if all(c['exit_code']==0 for c in checks) and integrity['delivery_gate']!='DELIVERY_FAIL' else 'FAIL',
            'checks':checks,'supply_chain_isolation':'UNVERIFIED','formal_delivery_admission':'NOT_GRANTED',
            'dl580_real_model_acceptance':'REQUIRES_GATEWAY_AND_HARDWARE_EVIDENCE'}
    result['receipt_hash']=trust.digest(result)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    out=args.output_dir/('MRL_LOCAL_ACCEPTANCE_'+uuid.uuid4().hex+'.json')
    with out.open('x',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert trust.load_json(out)==result
    print(json.dumps({'engineering':result['engineering'],'receipt':str(out),'receipt_hash':result['receipt_hash']},ensure_ascii=False))
    return 0 if result['engineering']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
