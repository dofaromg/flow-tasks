import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const MRL_ENDPOINTS = {
  status: '/api/mrl/status',
  convergence: '/api/mrl/runtime/convergence',
  persistentloop: '/api/mrl/runtime/persistentloop',
  worldGateway: '/api/mrl/world-gateway',
  product: '/api/mrl/product',
};

function StatusBadge({ status }) {
  const colors = {
    ACTIVE: { bg: '#dcfce7', border: '#16a34a', text: '#15803d' },
    STANDBY: { bg: '#fef9c3', border: '#ca8a04', text: '#a16207' },
    OFFLINE: { bg: '#fee2e2', border: '#dc2626', text: '#b91c1c' },
  };
  const c = colors[status] || colors.STANDBY;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 6,
      fontSize: '0.8rem',
      fontWeight: 700,
      background: c.bg,
      border: `1px solid ${c.border}`,
      color: c.text,
    }}>
      {status}
    </span>
  );
}

function SectionCard({ title, children }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      boxShadow: '0 2px 12px rgba(15,23,42,0.06)',
      border: '1px solid #e2e8f0',
      padding: '1.5rem',
      marginBottom: '1.25rem',
    }}>
      <h2 style={{ fontSize: '1.15rem', marginBottom: '1rem', color: '#0f172a' }}>{title}</h2>
      {children}
    </div>
  );
}

function DataRow({ label, value, mono }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
      <span style={{ color: '#64748b', fontSize: '0.9rem' }}>{label}</span>
      <span style={{ fontWeight: 600, fontSize: '0.9rem', fontFamily: mono ? 'monospace' : 'inherit', color: '#0f172a' }}>{value}</span>
    </div>
  );
}

export default function MRLOfficialWebsite() {
  const [statusData, setStatusData] = useState(null);
  const [convergenceData, setConvergenceData] = useState(null);
  const [loopData, setLoopData] = useState(null);
  const [gatewayData, setGatewayData] = useState(null);
  const [productData, setProductData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [statusRes, convergenceRes, loopRes, gatewayRes, productRes] = await Promise.allSettled([
          fetch(MRL_ENDPOINTS.status).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
          fetch(MRL_ENDPOINTS.convergence).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
          fetch(MRL_ENDPOINTS.persistentloop).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
          fetch(MRL_ENDPOINTS.worldGateway).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
          fetch(MRL_ENDPOINTS.product).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }),
        ]);
        if (statusRes.status === 'fulfilled') setStatusData(statusRes.value);
        if (convergenceRes.status === 'fulfilled') setConvergenceData(convergenceRes.value);
        if (loopRes.status === 'fulfilled') setLoopData(loopRes.value);
        if (gatewayRes.status === 'fulfilled') setGatewayData(gatewayRes.value);
        if (productRes.status === 'fulfilled') setProductData(productRes.value);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <Head>
        <title>MRL Official Platform | Mr.liou</title>
        <meta name="description" content="MRL Official Website Platform - Product Motherbody, World Gateway, Runtime Status" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="author" content="Mr.liou" />
      </Head>
      <div style={{
        minHeight: '100vh',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        background: '#0f172a',
        color: '#f8fafc',
      }}>
        {/* Header */}
        <header style={{
          borderBottom: '1px solid #1e293b',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', margin: 0, fontWeight: 800, letterSpacing: '-0.02em' }}>
              MRL Official Platform
            </h1>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#64748b' }}>
              Mr.liou Product Motherbody Engineering
            </p>
          </div>
          <nav style={{ display: 'flex', gap: '1.25rem', fontSize: '0.85rem' }}>
            <a href="#product" style={{ color: '#94a3b8', textDecoration: 'none' }}>Product</a>
            <a href="#gateway" style={{ color: '#94a3b8', textDecoration: 'none' }}>World Gateway</a>
            <a href="#runtime" style={{ color: '#94a3b8', textDecoration: 'none' }}>Runtime</a>
            <Link href="/" style={{ color: '#94a3b8', textDecoration: 'none' }}>Home</Link>
          </nav>
        </header>

        <main style={{ maxWidth: 960, margin: '0 auto', padding: '2rem 1.5rem' }}>
          {/* Hero */}
          <section style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <p style={{ color: '#38bdf8', fontWeight: 700, fontSize: '0.8rem', letterSpacing: 2, marginBottom: 8 }}>
              MRL PRODUCT MOTHERBODY
            </p>
            <h2 style={{ fontSize: '2.2rem', fontWeight: 800, margin: '0 0 0.75rem', lineHeight: 1.2 }}>
              MRL Official Website Platform
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '1rem', maxWidth: 600, margin: '0 auto' }}>
              Canonical runtime on DL580. Layer A ACTIVE_CPP_V1 signal source.
              PersistentLoop orchestration. BaseWorld state ledger. EntryGateway read interface.
            </p>
          </section>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading MRL runtime data...</div>
          ) : (
            <>
              {/* Product Entry */}
              <section id="product">
                <SectionCard title="MRL Product Entry">
                  {productData ? (
                    <>
                      <DataRow label="Product" value={productData.product} />
                      <DataRow label="Version" value={productData.version} />
                      <DataRow label="Canonical Runtime" value={productData.canonical_runtime} />
                      <DataRow label="Status" value={<StatusBadge status={productData.status} />} />
                      <DataRow label="Layer A" value={productData.layer_a} mono />
                      <DataRow label="PIDScope" value={productData.pid_scope} mono />
                      <DataRow label="Architecture" value={productData.architecture} />
                    </>
                  ) : <p style={{ color: '#94a3b8' }}>Product data unavailable</p>}
                </SectionCard>
              </section>

              {/* World Gateway */}
              <section id="gateway">
                <SectionCard title="MRL World Gateway">
                  {gatewayData ? (
                    <>
                      <DataRow label="Gateway" value={gatewayData.gateway} />
                      <DataRow label="Status" value={<StatusBadge status={gatewayData.status} />} />
                      <DataRow label="EntryGateway" value={gatewayData.entry_gateway} mono />
                      <DataRow label="Mode" value={gatewayData.mode} />
                      <DataRow label="External Services" value={gatewayData.external_services_role} />
                      {gatewayData.endpoints && (
                        <div style={{ marginTop: 8 }}>
                          <span style={{ color: '#64748b', fontSize: '0.85rem' }}>Available Endpoints:</span>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                            {gatewayData.endpoints.map(ep => (
                              <code key={ep} style={{ fontSize: '0.75rem', background: '#1e293b', padding: '2px 8px', borderRadius: 4, color: '#38bdf8' }}>{ep}</code>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : <p style={{ color: '#94a3b8' }}>Gateway data unavailable</p>}
                </SectionCard>
              </section>

              {/* Runtime Status */}
              <section id="runtime">
                <SectionCard title="Layer A - ACTIVE_CPP_V1">
                  {statusData ? (
                    <>
                      <DataRow label="Layer A Signal Source" value={statusData.layer_a.signal_source} mono />
                      <DataRow label="Status" value={<StatusBadge status={statusData.layer_a.status} />} />
                      <DataRow label="PIDScope" value={statusData.layer_a.pid_scope} mono />
                      <DataRow label="Canonical Runtime" value={statusData.canonical_runtime} />
                    </>
                  ) : <p style={{ color: '#94a3b8' }}>Layer A data unavailable</p>}
                </SectionCard>

                <SectionCard title="PersistentLoop / BaseWorld / EntryGateway">
                  {loopData ? (
                    <>
                      <DataRow label="PersistentLoop" value={loopData.persistent_loop.role} />
                      <DataRow label="PersistentLoop Status" value={<StatusBadge status={loopData.persistent_loop.status} />} />
                      <DataRow label="BaseWorld DB" value={loopData.base_world.role} />
                      <DataRow label="BaseWorld Status" value={<StatusBadge status={loopData.base_world.status} />} />
                      <DataRow label="EntryGateway" value={loopData.entry_gateway.role} />
                      <DataRow label="EntryGateway Status" value={<StatusBadge status={loopData.entry_gateway.status} />} />
                    </>
                  ) : <p style={{ color: '#94a3b8' }}>Loop data unavailable</p>}
                </SectionCard>

                <SectionCard title="Convergence API">
                  {convergenceData ? (
                    <>
                      <DataRow label="API" value={convergenceData.api} mono />
                      <DataRow label="Status" value={<StatusBadge status={convergenceData.status} />} />
                      <DataRow label="Threshold" value={convergenceData.convergence_threshold} />
                      <DataRow label="Engine" value={convergenceData.engine} />
                      <DataRow label="Last Check" value={convergenceData.last_check} />
                    </>
                  ) : <p style={{ color: '#94a3b8' }}>Convergence data unavailable</p>}
                </SectionCard>
              </section>

              {/* System Overview */}
              <SectionCard title="System Overview">
                {statusData ? (
                  <>
                    <DataRow label="Platform" value={statusData.platform} />
                    <DataRow label="Version" value={statusData.version} />
                    <DataRow label="Canonical Runtime" value={statusData.canonical_runtime} />
                    <DataRow label="Timestamp" value={statusData.timestamp} />
                  </>
                ) : <p style={{ color: '#94a3b8' }}>Status data unavailable</p>}
              </SectionCard>
            </>
          )}

          {/* Footer */}
          <footer style={{ textAlign: 'center', marginTop: '2rem', padding: '1.5rem', borderTop: '1px solid #1e293b', color: '#475569', fontSize: '0.8rem' }}>
            <p style={{ margin: 0 }}>MRL Official Platform | Mr.liou Product Motherbody Engineering v1</p>
            <p style={{ margin: '4px 0 0' }}>Canonical Runtime: DL580 | Layer A: ACTIVE_CPP_V1</p>
          </footer>
        </main>
      </div>
    </>
  );
}
