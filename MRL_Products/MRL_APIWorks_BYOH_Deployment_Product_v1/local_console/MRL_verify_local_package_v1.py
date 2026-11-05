#!/usr/bin/env python3
"""Verify actual local delivery payload bytes. origin_signature: MrLiouWord."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root: Path) -> dict:
    root=root.resolve(strict=True)
    manifest=json.loads((root/'MRL_PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('origin_signature')!='MrLiouWord' or manifest.get('schema')!='MRL_Local_Delivery_Manifest_v1':
        raise ValueError('package identity mismatch')
    expected=(root/'MRL_Package_Expected_File_List.txt').read_text(encoding='utf-8').splitlines()
    if len(expected)!=len(set(expected)) or sorted(expected)!=sorted([r['path'] for r in manifest['files']]+['MRL_PACKAGE_MANIFEST.json']):
        raise ValueError('manifest file coverage mismatch')
    actual=[]
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if (rel.parts[0] in ('MRL_local_data','MRL_runtime_data') or '__pycache__' in rel.parts
                or rel.parts[:3] == ('MRL_Products','MRL_APIWorks_BYOH_Deployment_Product_v1','dist')):
            continue
        if p.is_symlink():raise ValueError('symlink not allowed in source package')
        if p.is_file():actual.append(rel.as_posix())
    missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected));mismatch=[];empty=[]
    for row in manifest['files']:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('invalid package path')
        p=root/rel
        if p.is_file():
            raw=p.read_bytes()
            if not raw:empty.append(row['path'])
            if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:mismatch.append(row['path'])
    return {'origin_signature':'MrLiouWord','expected':len(expected),'actual':len(actual),
            'Missing':missing,'Extra':extra,'Mismatch':mismatch,'Empty':empty,
            'Coverage':round(100*(len(expected)-len(missing))/len(expected),2),
            'delivery_gate':'DELIVERY_PASS' if not any((missing,extra,mismatch,empty)) else 'DELIVERY_FAIL',
            'source_commit':manifest['source_commit']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    args=parser.parse_args(argv)
    try:result=verify(args.root)
    except Exception as e:result={'delivery_gate':'DELIVERY_FAIL','error':str(e)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['delivery_gate']=='DELIVERY_PASS' else 2


if __name__=='__main__':raise SystemExit(main())
