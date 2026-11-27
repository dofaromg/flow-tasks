#!/usr/bin/env python3
"""Build the complete offline console dependency closure. origin_signature: MrLiouWord."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from MRL_verify_local_package_v1 import verify

PRODUCT=Path(__file__).resolve().parents[1]
REPO=PRODUCT.parents[1]
PRODUCT_REL=PRODUCT.relative_to(REPO)
RUNTIME_REL=Path('MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1')
NAME='MRL_Runtime_Trust_Local_v1_1_0'
CONSOLE=(PRODUCT_REL/'local_console').as_posix()


def build(output:Path,source_commit:str):
    if not re.fullmatch('[0-9a-f]{40}',source_commit):raise ValueError('exact source commit required')
    for module in (PRODUCT/'scripts/MRL_verify_product_source_v1.py',REPO/RUNTIME_REL/'scripts/MRL_verify_package_v1.py'):
        subprocess.run([sys.executable,str(module)],cwd=REPO,check=True,capture_output=True)
    with tempfile.TemporaryDirectory() as temp:
        stage=Path(temp)/NAME;stage.mkdir()
        expected=set()
        for relative in (PRODUCT_REL,RUNTIME_REL):
            root=REPO/relative
            names=[x for x in (root/'EXPECTED_FILE_LIST.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
            for name in names:
                path=root/name
                if path.is_symlink() or not path.is_file() or not path.stat().st_size:
                    raise ValueError('missing/empty/symlink source: '+str(path))
                rel=(relative/name).as_posix();target=stage/rel
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
                expected.add(rel)
        wrapper={
            'Start_MRL.cmd':'@echo off\r\ncall "%~dp0'+CONSOLE.replace('/','\\')+'\\MRL_Start_Local.cmd" %*\r\n',
            'Run_Local_Acceptance.cmd':'@echo off\r\ncall "%~dp0'+CONSOLE.replace('/','\\')+'\\MRL_Accept_Local.cmd" %*\r\n',
            'Start_MRL.sh':'#!/bin/sh\nset -eu\nMRL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec sh "$MRL_ROOT/'+CONSOLE+'/MRL_Start_Local.sh" "$@"\n',
            'Run_Local_Acceptance.sh':'#!/bin/sh\nset -eu\nMRL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "${MRL_PYTHON:-python3}" "$MRL_ROOT/'+CONSOLE+'/MRL_accept_local_v1.py" "$@"\n',
        }
        for name,text in wrapper.items():(stage/name).write_bytes(text.encode('utf-8'))
        expected.update(wrapper)
        name='README_先讀我.md';(stage/name).write_bytes((PRODUCT/'local_console/README_zhTW.md').read_bytes());expected.add(name)
        name='MRL_LOCAL_PROVENANCE.json'
        provenance={'schema':'MRL_Local_Provenance_v1','origin_signature':'MrLiouWord',
                    'canonical_authority':'Mr.liou','version':NAME,'repository':'https://github.com/dofaromg/flow-tasks',
                    'source_commit':source_commit,'parent_commit':'bd4052bff5b96548a7fad8e618804e633525cfc5',
                    'original_paths_preserved':True,'runtime_binaries_or_weights_included':False,
                    'signature_profiles':['Ed25519 canonical MRL manifest'],
                    'production_policy':'UNCHANGED_EMPTY_ALLOWLIST'}
        (stage/name).write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');expected.add(name)
        expected.update(('MRL_Package_Expected_File_List.txt','MRL_PACKAGE_MANIFEST.json'))
        (stage/'MRL_Package_Expected_File_List.txt').write_text('\n'.join(sorted(expected))+'\n',encoding='utf-8')
        actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
        if actual!=expected-{'MRL_PACKAGE_MANIFEST.json'}:raise ValueError('staging coverage mismatch')
        rows=[]
        for name in sorted(actual):
            raw=(stage/name).read_bytes()
            if not raw:raise ValueError('empty payload: '+name)
            rows.append({'path':name,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        manifest={'schema':'MRL_Local_Delivery_Manifest_v1','origin_signature':'MrLiouWord',
                  'package_name':NAME,'source_commit':source_commit,'expected_file_count':len(expected),
                  'files':rows,'mutable_data_directories':['MRL_local_data','MRL_runtime_data',(PRODUCT_REL/'dist').as_posix()],
                  'dependency_tree':{'Start_MRL.cmd':[CONSOLE+'/MRL_Start_Local.cmd',CONSOLE+'/MRL_local_console_v1.py'],
                                     'console':[CONSOLE+'/index.html',(PRODUCT_REL/'scripts/MRL_artifact_trust_v1.py').as_posix(),(PRODUCT_REL/'scripts/MRL_capture_node_evidence_v1.py').as_posix()],
                                     'verification':[(PRODUCT_REL/'hardware/MRL_hardware_matrix_v1.json').as_posix(),(PRODUCT_REL/'trust/MRL_artifact_trust_policy_v1.json').as_posix()],
                                     'local_acceptance':['product tests','parent runtime','package checksum verification']},
                  'hardware_and_real_model_acceptance':'REQUIRES_USER_SERVER_EXECUTION'}
        (stage/'MRL_PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        audit=verify(stage)
        if audit['delivery_gate']!='DELIVERY_PASS':raise ValueError(audit)
        output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
        # A versioned output must not silently replace a previous delivery.
        with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
            for name in sorted(expected):
                info=zipfile.ZipInfo(NAME+'/'+name,date_time=(1980,1,1,0,0,0))
                info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,(stage/name).read_bytes())
        with zipfile.ZipFile(output) as z:
            names=z.namelist();wanted={NAME+'/'+n for n in expected}
            if len(names)!=len(set(names)) or set(names)!=wanted:raise ValueError('ZIP inventory mismatch')
            if any(z.read(NAME+'/'+n)!=(stage/n).read_bytes() for n in expected):raise ValueError('ZIP bytes mismatch')
        raw=output.read_bytes();checksum=hashlib.sha256(raw).hexdigest()
        sidecar=output.with_suffix('.zip.sha256')
        with sidecar.open('x',encoding='utf-8') as f:f.write(checksum+'  '+output.name+'\n')
        return {'delivery_gate':'DELIVERY_PASS','path':str(output),'sha256':checksum,'size':len(raw),
                'expected_file_count':len(expected),'actual_zip_count':len(names),'Missing':[],'Extra':[],
                'Mismatch':[],'Coverage':100,'source_commit':source_commit}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--source-commit',required=True);a=p.parse_args(argv)
    print(json.dumps(build(a.output,a.source_commit),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
