#!/usr/bin/env python3
"""Trusted MRL governance gate. Execute this file only from a trusted base ref."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="config/MRL_GOVERNANCE_PACKAGE_MANIFEST_v1.json"
SUMS="MRL_Mother/06_trace/MRL_GOVERNANCE_PACKAGE_SHA256SUMS_v1.txt"
NAMING="config/MRL_NAMING_LINEAGE_REGISTRY_v1.json"
HISTORY="config/MRL_HISTORICAL_EXTENSION_MAP_v1.json"
AUTH="config/MRL_AUTHORIZATION_REGISTRY_v1.json"
MIGRATIONS="config/MRL_MIGRATION_CONTRACTS_v1.json"
CRITICAL="config/MRL_CRITICAL_ASSET_INVENTORY_v1.json"
TRANSLATION="config/MRL_CLOUDFLARE_TRANSLATION_MAP_v1.json"
TRANSLATION_DOC="MRL_Mother/MRL_Adapters/Cloudflare/MRL_CLOUDFLARE_TRANSLATION_STATION_v1.md"
TRANSLATION_ENGINE="scripts/mrl_cloudflare_translation_station.py"
TRANSLATION_TEST="tests/test_mrl_cloudflare_translation_station.py"
LICENSE_SCOPE="config/MRL_LICENSE_SCOPE_REGISTRY_v1.json"
ROOT_AUTH="MRL_Mother/00_rootlaw/MRL_ROOT_AUTHORITY_v1.md"
RIGHTS="MRL_Mother/00_rootlaw/MRL_AUTHORIZATION_AND_OPERATING_RIGHTS_v1.md"
ROOTLAW="MRL_Mother/00_rootlaw/rootlaw.yaml"
ENGINE="MRL_Mother/09_workflow/MRL_FlowAgent_LawEngine_v1.py"
GUARD="MRL_Mother/09_workflow/MRL_OriginBoundary_Guard_v1.py"
IMMUTABLE=("MRL_Mother/MRL_MotherSource_Lineage_v1/","MRL_Mother/08_sources/","MRL_Mother/root_sources/")
IDENTIFIERS={"MrLiouWord","origin_signature","MRL","MRL_Mother","MrliouAI","FlowAgent","flowmemorysync"}
EXACT={"LICENSE","LICENSE_MrLiou_OpenSource_CC.md","vercel.json","flowos/wrangler.toml","particle-chat-v42/wrangler.toml","particle-edge-v4/wrangler.toml","vector-attention-engine/wrangler.jsonc","MRL_Mother/root_sources/wrangler.jsonc",ROOTLAW,ENGINE,GUARD,".github/CODEOWNERS",".github/workflows/mrl-root-governance-gate.yml","scripts/validate_mrl_governance.py"}
MIGRATION_FIELDS={"record_id","source_identifier","target_identifier","classification","compatibility_alias","dependency_set","data_effects","rollback","authorized_by","authorization_reference","verification","status"}
AUTH_FIELDS={"record_id","grantee","scope","actions","issued_by","issued_at","expires_at","evidence_reference","rollback"}
TRANSLATION_PARAMETERS={"delta_identity","delta_runtime","delta_source_root","delta_entrypoint","delta_build_method","delta_deploy_policy","delta_binding_contract","delta_trigger","delta_method_signature","delta_encoding_invariant","delta_history_return","delta_timing","delta_provenance"}
TRANSLATION_FORMULAS={"known_weight","mismatch_weight","total_weight","singularity_score","confidence","forward","reverse","round_trip","encoding"}
TRANSLATION_RETURN_FIELDS={"event_id","map_id","mapping_version","origin_signature","canonical_profile","provider","provider_kind","external_project","source_sha","build_id","parameter_snapshot","delta_vector","singularity_score","confidence","result","observed_at"}

class Failure(RuntimeError): pass
def fail(msg): raise Failure(msg)

def git(*args,allow_one=False):
    p=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
    if p.returncode and not (allow_one and p.returncode==1): fail(p.stderr.strip() or "git failed")
    return p.stdout

def read(path,ref=None):
    if ref: return git("show",f"{ref}:{path}")
    p=ROOT/path
    if not p.is_file(): fail(f"missing required file: {path}")
    return p.read_text(encoding="utf-8")

def exists(path,ref=None):
    if not ref: return (ROOT/path).is_file()
    p=subprocess.run(["git","cat-file","-e",f"{ref}:{path}"],cwd=ROOT,capture_output=True)
    return p.returncode==0

def real(path,ref=None):
    if not exists(path,ref): fail(f"missing required file: {path}")
    value=read(path,ref)
    if not value.strip() or value.strip().lower() in {"todo","tbd","placeholder","pending","{}","[]"}: fail(f"empty or placeholder file: {path}")
    return value

def obj(path,ref=None):
    try: value=json.loads(real(path,ref))
    except json.JSONDecodeError as e: fail(f"invalid JSON {path}: {e}")
    if not isinstance(value,dict): fail(f"JSON root is not object: {path}")
    return value

def tokens(path,required,ref=None):
    value=real(path,ref)
    for token in required:
        if token not in value: fail(f"{path} missing binding token: {token}")

def approved_migration(term,records,classification=None):
    for r in records:
        if not isinstance(r,dict) or not MIGRATION_FIELDS.issubset(r): continue
        if r.get("status")!="root-approved" or r.get("authorized_by")!="MrLiouWord" or not r.get("authorization_reference"): continue
        if classification and r.get("classification")!=classification: continue
        if not classification and r.get("source_identifier")!=term: continue
        return True
    return False

def validate_translation(ref=None):
    data=obj(TRANSLATION,ref)
    if data.get("schema_version")!="1.0.0" or data.get("origin_signature")!="MrLiouWord": fail("translation map identity mismatch")
    if not data.get("mapping_version") or data.get("map_id")!="MRL_Cloudflare_TranslationStation_v1": fail("translation map version missing")
    authority=data.get("authority",{})
    if authority.get("canonical_root")!="MRL" or authority.get("external_provider")!="Cloudflare" or authority.get("provider_role")!="adapter": fail("translation authority boundary mismatch")
    for flag in ("destructive_side_rewrite_allowed","implicit_name_equivalence_allowed","unknown_is_match","history_rewrite_allowed"):
        if authority.get(flag) is not False: fail(f"translation safety flag enabled: {flag}")
    if data.get("tri_state")!={"MATCH":0,"MISMATCH":1,"UNKNOWN":None}: fail("translation tri-state changed")

    parameters=data.get("inconsistency_parameters")
    if not isinstance(parameters,list): fail("translation parameters missing")
    parameter_ids=[]
    for item in parameters:
        if not isinstance(item,dict) or not isinstance(item.get("id"),str): fail("invalid translation parameter")
        if not isinstance(item.get("weight"),int) or item["weight"]<=0 or not isinstance(item.get("critical"),bool): fail(f"invalid translation parameter contract: {item.get('id')}")
        parameter_ids.append(item["id"])
    if set(parameter_ids)!=TRANSLATION_PARAMETERS or len(parameter_ids)!=len(set(parameter_ids)): fail("translation parameter coverage mismatch")
    if not TRANSLATION_FORMULAS.issubset(data.get("formulas",{})): fail("translation formula coverage mismatch")

    profiles=data.get("canonical_profiles")
    if not isinstance(profiles,list) or not profiles: fail("canonical translation profiles missing")
    profile_ids=[]
    profile_map={}
    for profile in profiles:
        if not isinstance(profile,dict) or not isinstance(profile.get("id"),str) or not profile.get("canonical_identity") or not profile.get("deploy_policy"): fail("invalid canonical translation profile")
        profile_ids.append(profile["id"]); profile_map[profile["id"]]=profile
    if len(profile_ids)!=len(set(profile_ids)): fail("duplicate canonical translation profile")

    nodes=data.get("external_nodes")
    if not isinstance(nodes,list) or len(nodes)!=4: fail("Cloudflare external-node coverage mismatch")
    node_keys=[]
    for node in nodes:
        if not isinstance(node,dict): fail("invalid external translation node")
        key=(node.get("provider_kind"),node.get("external_project")); node_keys.append(key)
        if key[0] not in {"pages","workers"} or not isinstance(key[1],str): fail("invalid external translation identity")
        candidate=node.get("candidate_profile")
        if candidate not in profile_map: fail(f"unknown translation candidate: {candidate}")
        if node.get("link_state")!="active_verified" and node.get("forward_action")!="HOLD": fail(f"unverified translation node can deploy: {key}")
        if profile_map[candidate].get("deploy_policy") in {"gke_gitops","requires_explicit_deployment","local_backfill_no_deploy"} and node.get("forward_action")!="HOLD": fail(f"no-deploy translation node can deploy: {key}")
        vector=node.get("delta_states",{})
        if set(vector)!=TRANSLATION_PARAMETERS or not set(vector.values()).issubset({"MATCH","MISMATCH","UNKNOWN"}): fail(f"translation delta vector invalid: {key}")
        if not re.fullmatch(r"[0-9a-f]{40}",str(node.get("observed_source_sha",""))): fail(f"translation source SHA invalid: {key}")
    if len(node_keys)!=len(set(node_keys)): fail("duplicate Cloudflare external translation node")
    mrl_store=next((n for n in nodes if n.get("provider_kind")=="workers" and n.get("external_project")=="mrl-store"),{})
    if mrl_store.get("link_state")!="unverified_name_similarity_only" or mrl_store.get("delta_states",{}).get("delta_identity")!="UNKNOWN": fail("mrl-store identity was inferred")

    history=data.get("method_change_history")
    if not isinstance(history,list) or len(history)<3 or any(item.get("method")!="utf8ToBase64" for item in history if isinstance(item,dict)): fail("translation method-change history incomplete")
    times=[item.get("observed_at") for item in history]
    if times!=sorted(times): fail("translation method-change history unordered")
    if not TRANSLATION_RETURN_FIELDS.issubset(data.get("return_evidence_fields",[])): fail("translation return evidence incomplete")
    if len(data.get("invariants",[]))<7: fail("translation invariants incomplete")
    tokens(TRANSLATION_DOC,["Three-state difference model","Forward translation","Reverse translation","Round-trip invariant","UTF-8/Base64 method invariant","`UNKNOWN` is never converted to `MATCH`"],ref)
    tokens(TRANSLATION_ENGINE,["def validate_registry","def score_delta_vector","def translate_forward","def translate_reverse","def verify_encoding_invariant","sanitize_snapshot"],ref)
    tokens(TRANSLATION_TEST,["test_unknown_critical_parameters_never_pass","test_verified_synthetic_link_round_trips_without_renaming","test_encoding_formula_is_chunk_invariant_for_unicode_and_large_input"],ref)
    return {"parameters":len(parameter_ids),"canonical_profiles":len(profile_ids),"external_nodes":len(nodes),"method_changes":len(history)}

def validate_static(ref=None):
    manifest=obj(MANIFEST,ref)
    artifacts=manifest.get("artifacts")
    if not isinstance(artifacts,list) or manifest.get("expected_file_count")!=len(artifacts): fail("manifest count mismatch")
    paths=[]
    for item in artifacts:
        if not isinstance(item,dict) or not isinstance(item.get("path"),str): fail("manifest artifact path missing")
        path=item["path"]
        if path in paths: fail(f"duplicate artifact: {path}")
        paths.append(path); real(path,ref)
        if not isinstance(item.get("dependencies"),list): fail(f"dependencies missing: {path}")
        for dep in item["dependencies"]:
            if dep not in paths and not exists(dep,ref): fail(f"missing dependency {dep} for {path}")
    sums={}
    for number,line in enumerate(real(SUMS,ref).splitlines(),1):
        if not line.strip(): continue
        m=re.fullmatch(r"([0-9a-f]{64})  (.+)",line)
        if not m: fail(f"invalid SHA line {number}")
        sums[m.group(2)]=m.group(1)
    expected=set(paths)-{SUMS}
    if set(sums)!=expected: fail(f"SHA coverage mismatch missing={sorted(expected-set(sums))} extra={sorted(set(sums)-expected)}")
    for path,digest in sums.items():
        if hashlib.sha256(read(path,ref).encode()).hexdigest()!=digest: fail(f"SHA mismatch: {path}")

    naming=obj(NAMING,ref)
    if naming.get("origin_signature")!="MrLiouWord" or naming.get("canonical_root")!="MRL": fail("naming root mismatch")
    hierarchy=naming.get("hierarchy",{})
    for name in ("MRL_Mother","MrliouAI","FlowAgent","flowmemorysync"):
        if hierarchy.get(name,{}).get("parent")!="MRL": fail(f"lineage mismatch: {name}")
    if hierarchy.get("FlowAgent",{}).get("preserve_exact_identity") is not True: fail("FlowAgent identity is not preserved")
    if not set(IMMUTABLE).issubset(naming.get("immutable_lineage_prefixes",[])): fail("immutable floor weakened")
    if not IDENTIFIERS.issubset(naming.get("protected_identifiers",[])): fail("identifier floor weakened")
    if not EXACT.issubset(naming.get("protected_exact_paths",[])): fail("exact-path floor weakened")
    rc=naming.get("rename_contract",{})
    if rc.get("classification_before_transform") is not True or rc.get("global_string_replace_allowed") is not False or rc.get("lineage_preservation_required") is not True: fail("rename contract weakened")
    if not MIGRATION_FIELDS.issubset(rc.get("required_fields",[])): fail("migration fields weakened")

    history=obj(HISTORY,ref); policy=history.get("policy",{})
    for key in ("classification_before_transformation","external_assets_remain_external","mrl_assets_must_not_be_reduced","historical_lineage_preserved","flowagent_is_mrl_native_product_module"):
        if policy.get(key) is not True: fail(f"historical policy false: {key}")
    if policy.get("global_destructive_rename_allowed") is not False or policy.get("implicit_authorization_allowed") is not False: fail("historical destructive policy enabled")
    flow=next((x for x in history.get("mappings",[]) if x.get("source")=="FlowAgent"),{})
    if flow.get("classification")!="mrl_native_product_module" or flow.get("rename_allowed") is not False or flow.get("replace_with_mrliouai") is not False: fail("FlowAgent classification invalid")

    auth=obj(AUTH,ref); model=auth.get("authorization_model",{})
    if model.get("default_decision")!="DENY" or model.get("explicit_grant_required") is not True: fail("authorization default invalid")
    false_flags=("implicit_authorization_allowed","repository_access_is_authorization","collaborator_role_is_authorization","bot_or_agent_execution_is_authorization","prior_contribution_is_authorization","technical_capability_is_authorization","silence_is_authorization","restoration_is_authorization","operating_grant_transfers_authorship","operating_grant_transfers_founder_status","operating_grant_transfers_commercial_rights")
    if any(model.get(k) is not False for k in false_flags): fail("authorization inference or rights transfer enabled")
    grants=auth.get("active_grants")
    if not isinstance(grants,list): fail("active grants is not a list")
    for grant in grants:
        if not AUTH_FIELDS.issubset(grant) or grant.get("issued_by")!="MrLiouWord": fail("invalid authorization grant")

    mig=obj(MIGRATIONS,ref)
    if mig.get("default_decision")!="DENY" or mig.get("contract",{}).get("global_replace_allowed") is not False: fail("migration default invalid")
    if not MIGRATION_FIELDS.issubset(mig.get("contract",{}).get("required_fields",[])): fail("migration schema weakened")
    for r in mig.get("migrations",[]):
        if not MIGRATION_FIELDS.issubset(r): fail("incomplete migration record")
        if r.get("status")=="root-approved" and (r.get("authorized_by")!="MrLiouWord" or not r.get("authorization_reference")): fail("unbound root approval")

    lic=obj(LICENSE_SCOPE,ref)
    if lic.get("whole_repository_inference_allowed") is not False or lic.get("commercial_permission_inference_allowed") is not False or lic.get("third_party_delegation_inference_allowed") is not False: fail("license scope inference enabled")

    tokens(ROOT_AUTH,["origin_signature: MrLiouWord","root_authority: Mr.liou","canonical_root: MRL","FlowAgent is an MRL-native product identity","In the absence of a matching authorization record, the decision is DENY","Classification precedes transformation"],ref)
    tokens(RIGHTS,["default_decision: DENY","No permission is inferred","A grant to operate does not transfer authorship"],ref)
    tokens(ROOTLAW,["version: 11","amd_v11_classification_authorization","rl_21_classification_before_reclamation_and_explicit_authorization"],ref)
    tokens(ENGINE,["def load_native_identities","def is_mrl_native_name",'names = {"FlowAgent"}',"if is_mrl_native_name(raw):","return raw"],ref)
    tokens(GUARD,["def is_mrl_manifestable_identity",'native = is_mrl_native_name(external_name)','"mrl_native_product" if native else "external_material"'],ref)
    for item in obj(CRITICAL,ref).get("required_files",[]):
        if not isinstance(item,dict) or not isinstance(item.get("path"),str): fail("critical inventory entry invalid")
        real(item["path"],ref)
    translation=validate_translation(ref)
    return {"expected":len(paths),"present":len(paths),"sha256_covered":len(sums),"translation":translation}

def term_count(ref,term):
    out=git("grep","-I","-o","-F","--no-color","-e",term,ref,"--",".",allow_one=True)
    return len(out.splitlines()) if out else 0

def validate_diff(base,head):
    records=obj(MIGRATIONS,head).get("migrations",[])
    rows=[]
    for line in git("diff","--name-status","-M",f"{base}...{head}").splitlines():
        parts=line.split("\t")
        if len(parts)>=2: rows.append((parts[0],parts[1:]))
    for status,paths in rows:
        old,new=paths[0],paths[-1]
        if (status.startswith("D") or status.startswith("R")) and (old in EXACT or new in EXACT or old.startswith(IMMUTABLE) or new.startswith(IMMUTABLE)): fail(f"protected delete/rename: {status} {paths}")
        if status.startswith("M") and old.startswith(IMMUTABLE): fail(f"immutable lineage modified: {old}")
    counts={}
    for term in sorted(IDENTIFIERS):
        before,after=term_count(base,term),term_count(head,term); counts[term]={"base":before,"head":after}
        if after<before and not approved_migration(term,records): fail(f"protected identifier reduced without root approval: {term} {before}->{after}")
    threshold=int(obj(NAMING,head).get("rename_contract",{}).get("mass_change_file_threshold",100))
    if len(rows)>=threshold and not approved_migration(None,records,"mass_change"): fail(f"unapproved mass change: {len(rows)} files")
    return {"changed_files":len(rows),"identifier_counts":counts}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--base"); p.add_argument("--head"); p.add_argument("--ref"); a=p.parse_args()
    if bool(a.base)!=bool(a.head): fail("--base and --head must be used together")
    ref=a.head or a.ref
    result={"origin_signature":"MrLiouWord","canonical_root":"MRL","status":"DELIVERY_FAIL","delivery":validate_static(ref)}
    if a.base: result["diff"]=validate_diff(a.base,a.head)
    result.update(status="DELIVERY_PASS",coverage="100%")
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))

if __name__=="__main__":
    try: main()
    except Failure as e:
        print(f"MRL_GOVERNANCE_GATE_FAIL: {e}",file=sys.stderr); raise SystemExit(1)
