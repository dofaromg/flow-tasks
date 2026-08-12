import Head from 'next/head';
import { useCallback, useEffect, useMemo, useState } from 'react';

const ENDPOINTS = {
  status: '/api/mrl/status',
  convergence: '/api/mrl/runtime/convergence',
  persistentLoop: '/api/mrl/runtime/persistentloop',
  worldGateway: '/api/mrl/world-gateway',
  product: '/api/mrl/product',
};

const TABS = [
  { id: 'control', label: '主控', icon: '◉' },
  { id: 'runtime', label: '執行', icon: '↯' },
  { id: 'memory', label: '記憶', icon: '◇' },
  { id: 'world', label: '世界', icon: '◎' },
  { id: 'audit', label: '審核', icon: '✓' },
];

function normalizeStatus(value) {
  const text = String(value || 'UNKNOWN').toUpperCase();
  if (['ACTIVE', 'PASS', 'ONLINE', 'HEALTHY', 'READY'].includes(text)) return 'ACTIVE';
  if (['OFFLINE', 'FAIL', 'ERROR', 'DOWN'].includes(text)) return 'OFFLINE';
  return 'STANDBY';
}

function StatusPill({ value }) {
  const status = normalizeStatus(value);
  const palette = {
    ACTIVE: ['#092d24', '#29d391', '#84f1c6'],
    STANDBY: ['#352b0d', '#f4c542', '#ffe28a'],
    OFFLINE: ['#3a1418', '#ff6575', '#ff9da8'],
  }[status];

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      border: `1px solid ${palette[1]}55`, background: palette[0], color: palette[2],
      borderRadius: 999, padding: '5px 9px', fontSize: 11, fontWeight: 800,
      letterSpacing: '.04em', whiteSpace: 'nowrap',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: 999, background: palette[1], boxShadow: `0 0 12px ${palette[1]}` }} />
      {status}
    </span>
  );
}

function Card({ title, subtitle, right, children }) {
  return (
    <section style={{
      background: 'linear-gradient(180deg, rgba(22,31,48,.96), rgba(13,20,33,.96))',
      border: '1px solid rgba(148,163,184,.15)', borderRadius: 20,
      padding: 16, boxShadow: '0 18px 45px rgba(0,0,0,.22)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', marginBottom: children ? 14 : 0 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 850, letterSpacing: '-.01em' }}>{title}</h2>
          {subtitle ? <p style={{ margin: '4px 0 0', color: '#7f91aa', fontSize: 11, lineHeight: 1.45 }}>{subtitle}</p> : null}
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value, mono = false, valueNode = null }) {
  return (
    <div style={{ padding: '11px 0', borderTop: '1px solid rgba(148,163,184,.09)', display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
      <span style={{ color: '#8190a5', fontSize: 12 }}>{label}</span>
      {valueNode || <span style={{ color: '#eef5ff', fontSize: 12, fontWeight: 750, textAlign: 'right', fontFamily: mono ? 'ui-monospace,SFMono-Regular,Menlo,monospace' : 'inherit', overflowWrap: 'anywhere' }}>{value ?? '—'}</span>}
    </div>
  );
}

function EndpointAudit({ name, result }) {
  const ok = result?.ok === true;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10, padding: '10px 0', borderTop: '1px solid rgba(148,163,184,.09)' }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 750 }}>{name}</div>
        <div style={{ color: '#6f8098', fontSize: 10, marginTop: 3, fontFamily: 'ui-monospace,SFMono-Regular,Menlo,monospace' }}>{result?.endpoint}</div>
      </div>
      <span style={{ color: ok ? '#84f1c6' : '#ffe28a', fontSize: 10, fontWeight: 850, alignSelf: 'center' }}>{ok ? 'VERIFIED' : 'UNAVAILABLE'}</span>
    </div>
  );
}

export default function MrliouMobile() {
  const [tab, setTab] = useState('control');
  const [data, setData] = useState({});
  const [audit, setAudit] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    const entries = Object.entries(ENDPOINTS);
    const results = await Promise.allSettled(entries.map(([, endpoint]) => fetch(endpoint, { cache: 'no-store' }).then(async (r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })));

    const nextData = {};
    const nextAudit = {};
    results.forEach((result, index) => {
      const [key, endpoint] = entries[index];
      if (result.status === 'fulfilled') {
        nextData[key] = result.value;
        nextAudit[key] = { ok: true, endpoint };
      } else {
        nextAudit[key] = { ok: false, endpoint, error: result.reason?.message || 'unavailable' };
      }
    });
    setData(nextData);
    setAudit(nextAudit);
    setLastRefresh(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 30000);
    return () => clearInterval(timer);
  }, [refresh]);

  const verifiedCount = useMemo(() => Object.values(audit).filter((x) => x.ok).length, [audit]);
  const totalCount = Object.keys(ENDPOINTS).length;
  const status = data.status;
  const product = data.product;
  const loop = data.persistentLoop;
  const gateway = data.worldGateway;
  const convergence = data.convergence;

  return (
    <>
      <Head>
        <title>Mrliou Mobile | MRL</title>
        <meta name="description" content="Mrliou mobile control interface for MRL runtime, memory, world gateway and audit state." />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="#07101d" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </Head>

      <div style={{ minHeight: '100dvh', background: 'radial-gradient(circle at 50% -20%, #173657 0, #091320 35%, #050b13 72%)', color: '#eef5ff', fontFamily: 'Inter,-apple-system,BlinkMacSystemFont,"SF Pro Display",system-ui,sans-serif' }}>
        <div style={{ maxWidth: 520, margin: '0 auto', minHeight: '100dvh', padding: 'max(18px, env(safe-area-inset-top)) 14px calc(94px + env(safe-area-inset-bottom))' }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 2px 18px' }}>
            <div>
              <div style={{ color: '#55c7ff', fontSize: 10, fontWeight: 900, letterSpacing: '.18em' }}>MRL MOBILE NODE</div>
              <h1 style={{ margin: '4px 0 0', fontSize: 25, letterSpacing: '-.04em' }}>Mrliou</h1>
            </div>
            <button onClick={refresh} disabled={loading} aria-label="Refresh MRL runtime data" style={{ width: 42, height: 42, borderRadius: 14, border: '1px solid rgba(85,199,255,.22)', background: 'rgba(15,31,50,.8)', color: '#9bdcff', fontSize: 18, cursor: 'pointer' }}>
              {loading ? '…' : '↻'}
            </button>
          </header>

          <div style={{ display: 'grid', gap: 12 }}>
            {tab === 'control' && (
              <>
                <Card title="母體狀態" subtitle="直接讀取既有 MRL runtime API，不以 UI 自行宣告完成。" right={<StatusPill value={status?.layer_a?.status || product?.status} />}>
                  <Metric label="Canonical Runtime" value={status?.canonical_runtime || product?.canonical_runtime} />
                  <Metric label="Layer A" value={status?.layer_a?.signal_source || product?.layer_a} mono />
                  <Metric label="Product" value={product?.product} />
                  <Metric label="Version" value={product?.version || status?.version} />
                </Card>

                <Card title="即時驗證" subtitle="目前手機介面可讀取的工程端點。" right={<span style={{ color: '#84f1c6', fontSize: 12, fontWeight: 850 }}>{verifiedCount}/{totalCount}</span>}>
                  <Metric label="Runtime API Coverage" value={`${verifiedCount} / ${totalCount}`} />
                  <Metric label="Refresh" value={lastRefresh ? lastRefresh.toLocaleTimeString() : '—'} />
                  <Metric label="Verification Rule" value="Evidence > UI claim" mono />
                </Card>
              </>
            )}

            {tab === 'runtime' && (
              <>
                <Card title="PersistentLoop" subtitle="執行循環與狀態協調。" right={<StatusPill value={loop?.persistent_loop?.status} />}>
                  <Metric label="Role" value={loop?.persistent_loop?.role} />
                  <Metric label="Convergence Engine" value={convergence?.engine} />
                  <Metric label="Threshold" value={convergence?.convergence_threshold} />
                  <Metric label="Last Check" value={convergence?.last_check} />
                </Card>
                <Card title="Layer A" subtitle="目前 runtime signal source。" right={<StatusPill value={status?.layer_a?.status} />}>
                  <Metric label="Signal Source" value={status?.layer_a?.signal_source} mono />
                  <Metric label="PID Scope" value={status?.layer_a?.pid_scope || product?.pid_scope} mono />
                </Card>
              </>
            )}

            {tab === 'memory' && (
              <>
                <Card title="BaseWorld Memory" subtitle="以現有 PersistentLoop API 顯示 BaseWorld 狀態，不虛構新的記憶後端。" right={<StatusPill value={loop?.base_world?.status} />}>
                  <Metric label="Role" value={loop?.base_world?.role} />
                  <Metric label="State Source" value="PersistentLoop API" mono />
                </Card>
                <Card title="EntryGateway" subtitle="記憶與世界狀態的讀取入口。" right={<StatusPill value={loop?.entry_gateway?.status} />}>
                  <Metric label="Role" value={loop?.entry_gateway?.role} />
                  <Metric label="Gateway" value={gateway?.entry_gateway} mono />
                </Card>
              </>
            )}

            {tab === 'world' && (
              <Card title="World Gateway" subtitle="外部世界僅透過 gateway 映射，不由手機 UI 覆寫核心狀態。" right={<StatusPill value={gateway?.status} />}>
                <Metric label="Gateway" value={gateway?.gateway} />
                <Metric label="Mode" value={gateway?.mode} />
                <Metric label="External Role" value={gateway?.external_services_role} />
                <div style={{ paddingTop: 12, borderTop: '1px solid rgba(148,163,184,.09)' }}>
                  <div style={{ color: '#8190a5', fontSize: 11, marginBottom: 8 }}>Exposed endpoints</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                    {(gateway?.endpoints || []).map((ep) => <code key={ep} style={{ color: '#9bdcff', background: '#07182a', border: '1px solid rgba(85,199,255,.15)', padding: '6px 8px', borderRadius: 10, fontSize: 10 }}>{ep}</code>)}
                    {!gateway?.endpoints?.length && <span style={{ color: '#66778e', fontSize: 11 }}>No endpoint data returned.</span>}
                  </div>
                </div>
              </Card>
            )}

            {tab === 'audit' && (
              <>
                <Card title="Runtime Evidence Audit" subtitle="成功讀到端點才標 VERIFIED；讀不到只標 UNAVAILABLE，不反推不存在。">
                  {Object.entries(ENDPOINTS).map(([key]) => <EndpointAudit key={key} name={key} result={audit[key]} />)}
                </Card>
                <Card title="MRL 工作流" subtitle="建構、保存、顯化、審核分層。">
                  <Metric label="Engineering" value="GitHub" />
                  <Metric label="Record / Evidence" value="Notion" />
                  <Metric label="Artifact Storage" value="Google Drive" />
                  <Metric label="Visualization" value="Mrliou Mobile" />
                  <Metric label="Consistency Audit" value="MRL Audit" />
                  <Metric label="Final Approval" value="Human owner" />
                </Card>
              </>
            )}
          </div>
        </div>

        <nav aria-label="Mrliou mobile navigation" style={{ position: 'fixed', left: '50%', transform: 'translateX(-50%)', bottom: 0, width: 'min(520px, 100%)', padding: '9px 12px calc(9px + env(safe-area-inset-bottom))', background: 'rgba(5,11,19,.88)', borderTop: '1px solid rgba(148,163,184,.13)', backdropFilter: 'blur(18px)', WebkitBackdropFilter: 'blur(18px)', zIndex: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${TABS.length},1fr)`, gap: 4 }}>
            {TABS.map((item) => {
              const active = tab === item.id;
              return (
                <button key={item.id} onClick={() => setTab(item.id)} style={{ border: 0, background: active ? 'rgba(85,199,255,.11)' : 'transparent', color: active ? '#9bdcff' : '#687a92', borderRadius: 14, padding: '8px 2px 7px', cursor: 'pointer' }}>
                  <div style={{ fontSize: 17, lineHeight: 1 }}>{item.icon}</div>
                  <div style={{ fontSize: 9, fontWeight: 800, marginTop: 5 }}>{item.label}</div>
                </button>
              );
            })}
          </div>
        </nav>
      </div>
    </>
  );
}
