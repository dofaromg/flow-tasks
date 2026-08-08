# -*- coding: utf-8 -*-
# Batch04 CrossCheck round 1: page-1 Notion raw.json vs DL580 runtime wave receipts.
# String-level concept matching. Runs on DL580.
import json, os, glob

NOTION_RAW=r"D:\MRL_Mother\EvidenceChain\_sources\Notion\Mrliou_MRL_MrLiouAI.raw.json"
WAVES_DIR=r"D:\MRL_Mother\runtime\waves"

notion_concepts=["MrLiouAI","Fluin","SEED","δP₀","Layer","Law Layer","Zoom Engine",
 "MemoryLayer","CollapseEngine","Particle","粒子","反推","映射","地球儀",
 "Flow_SymbolicReason","Flow_ProbReason","Flow_Fuse","Flow_Planner","Flow_Control",
 "Flow_ToolUse","Flow_Orchestrate","Flow_Explain"]
dl580_concepts=["Wave01","Wave02","Wave09","gates.total","gates.pass","origin_signature",
 "MrLiouWord","receipt","registry","mrl.flow","runtime","gate"]

# load notion page1 text (raw json as string -> count concept occurrences)
ntext=open(NOTION_RAW,encoding="utf-8").read()
def count(hay,needle): 
    return hay.count(needle)

ncounts={c:count(ntext,c) for c in notion_concepts}

# load all wave receipts text (concatenate) for DL580 side
dtext=""
for f in sorted(glob.glob(os.path.join(WAVES_DIR,"wave*","*Gate_Receipt.json"))):
    try: dtext+=open(f,encoding="utf-8-sig").read()
    except: 
        try: dtext+=open(f,encoding="utf-8").read()
        except: pass
dcounts={c:count(dtext,c) for c in dl580_concepts}

# also check: do any notion concepts appear on DL580 side, and vice versa
rows=[]
# For each notion concept, see if it also appears in DL580 runtime text
for nc in notion_concepts:
    nmatch=ncounts[nc]
    dmatch=count(dtext,nc)
    if nmatch>0 and dmatch>0: status="string_cross_match"
    elif nmatch>0 and dmatch==0: status="notion_only"
    elif nmatch==0 and dmatch>0: status="runtime_only"
    else: status="pending_review"
    # pick best dl580 target concept that co-occurs
    target=""
    if dmatch>0: target="wave_gate_receipts(text)"
    rows.append({"notion_page":"Mrliou_MRL_MrLiouAI","notion_concept":nc,
                 "notion_match_count":nmatch,"dl580_match_target":target or "wave_gate_receipts",
                 "dl580_match_count":dmatch,
                 "relation_type":"concept_string","status":status,
                 "notes":""})
# Also report DL580-native concept presence (runtime_only baseline)
for dc in dl580_concepts:
    nmatch=count(ntext,dc); dmatch=dcounts[dc]
    if nmatch>0 and dmatch>0: status="string_cross_match"
    elif dmatch>0 and nmatch==0: status="runtime_only"
    elif nmatch>0 and dmatch==0: status="notion_only"
    else: status="pending_review"
    rows.append({"notion_page":"Mrliou_MRL_MrLiouAI","notion_concept":dc+"(dl580_term)",
                 "notion_match_count":nmatch,"dl580_match_target":"wave_gate_receipts",
                 "dl580_match_count":dmatch,"relation_type":"runtime_term",
                 "status":status,"notes":"dl580-origin term checked against notion page"})

_out={"rows":rows,"notion_concepts_present":sum(1 for c in notion_concepts if ncounts[c]>0),"cross_matches":sum(1 for r in rows if r["status"]=="string_cross_match")}
open(r"D:\MRL_Mother\EvidenceChain\_reports\_cc_raw.json","w",encoding="utf-8").write(json.dumps(_out,ensure_ascii=False))
print("WROTE_CC rows="+str(len(rows)))
