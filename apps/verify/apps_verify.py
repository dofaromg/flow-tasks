"""apps core verification — stdlib only. origin_signature: MrLiouWord"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))

def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, '..', rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

mod_a = load('mod_a_core', 'module-a/core.py')
orch  = load('orch_core',  'orchestrator/core.py')

P=[0]; F=[0]
def c(name, cond, d=''):
    if cond: P[0]+=1; print('  ✅', name)
    else: F[0]+=1; print('  ❌', name, d)

print('== module-a core ==')
r = mod_a.compute_particle('MrLiou particle particle test')
c('token_count correct', r['token_count'] == 4, r)
c('unique_tokens correct', r['unique_tokens'] == 3, r)
c('sha256 is 64 hex', len(r['sha256']) == 64)
c('simhash64 is 16 hex', len(r['simhash64']) == 16)
c('particle_score deterministic', mod_a.compute_particle('MrLiou particle particle test')['particle_score'] == r['particle_score'])
c('empty text -> score 0', mod_a.compute_particle('')['particle_score'] == 0.0)
try:
    mod_a.compute_particle(123); c('non-string raises', False)
except ValueError: c('non-string raises ValueError', True)
h1 = mod_a.compute_particle('the quick brown fox jumps')['simhash64']
h2 = mod_a.compute_particle('the quick brown fox jumps')['simhash64']
h3 = mod_a.compute_particle('completely different words here now')['simhash64']
c('identical text same simhash', h1 == h2)
c('different text differs', h1 != h3)
c('capabilities lists compute', 'compute_particle' in mod_a.capabilities()['capabilities'])

print('== orchestrator core ==')
res = orch.run_pipeline({'items': ['hello world', 'hello world', 'a totally distinct sentence']}, mod_a.compute_particle)
c('pipeline success', res['orchestrator'] == 'success')
c('summary items = 3', res['summary']['items'] == 3, res['summary'])
c('dedup: 2 unique (exact dup removed)', res['summary']['unique_particles'] == 2, res['summary'])
c('total_tokens = 8', res['summary']['total_tokens'] == 8, res['summary'])
c('trace steps ordered', [s['step'] for s in res['trace']] == ['validate','compute','dedup','aggregate'], res['trace'])
c('hamming identical = 0', orch.hamming_hex(h1, h2) == 0)
c('hamming differs > 0', orch.hamming_hex(h1, h3) > 0)
try:
    orch.run_pipeline({'items': []}, mod_a.compute_particle); c('empty items raises', False)
except ValueError: c('empty items raises ValueError', True)
try:
    orch.run_pipeline({}, mod_a.compute_particle); c('missing items raises', False)
except ValueError: c('missing items raises ValueError', True)

print(f"\n===== apps cores: {P[0]} passed, {F[0]} failed =====")
sys.exit(1 if F[0] else 0)
