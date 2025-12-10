import Head from 'next/head';

const features = [
  '一鍵部署 GKE 基礎設施與 GitOps 設定',
  '預設 CI/CD 流程，推送即可自動驗證與部署',
  '可觀察性與調試友善：結構化配置、可重複的腳本',
];

export default function Home() {
  return (
    <>
      <Head>
        <title>Flow Tasks</title>
        <meta
          name="description"
          content="FlowAgent GKE Starter：快速部署、GitOps、CI/CD 的參考範本。"
        />
      </Head>
      <main
        style={{
          minHeight: '100vh',
          display: 'grid',
          placeItems: 'center',
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
          background: 'radial-gradient(circle at 20% 20%, #e0f2fe 0, transparent 25%), radial-gradient(circle at 80% 10%, #fee2e2 0, transparent 25%), #f8fafc',
          color: '#0f172a',
          padding: '3rem 1.5rem',
        }}
      >
        <section
          style={{
            maxWidth: 720,
            width: '100%',
            background: '#ffffff',
            borderRadius: 16,
            boxShadow: '0 16px 48px rgba(15, 23, 42, 0.08)',
            padding: '2.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <p style={{ color: '#64748b', fontWeight: 600, letterSpacing: 1.2, marginBottom: 12 }}>
            FLOWAGENT GKE STARTER
          </p>
          <h1 style={{ fontSize: '2.5rem', margin: '0 0 1rem', lineHeight: 1.2 }}>
            快速啟動你的雲端 GitOps 與 CI/CD
          </h1>
          <p style={{ color: '#475569', marginBottom: '1.5rem', fontSize: '1.05rem', lineHeight: 1.7 }}>
            以同一套配置管理 Kubernetes、CI/CD、與部署快照。複製、推送、開啟驗證腳本，即可把服務穩定送上線。
          </p>

          <div
            style={{
              display: 'grid',
              gap: '0.75rem',
              marginBottom: '2rem',
            }}
          >
            {features.map((feature) => (
              <div
                key={feature}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.85rem 1rem',
                  background: '#f8fafc',
                  borderRadius: 10,
                  border: '1px solid #e2e8f0',
                  fontWeight: 600,
                  color: '#0f172a',
                }}
              >
                <span
                  aria-hidden
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    background: '#0ea5e9',
                    color: '#fff',
                    fontSize: '0.9rem',
                  }}
                >
                  ✓
                </span>
                {feature}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
            <a
              href="https://github.com/dofaromg/flow-tasks"
              style={{
                background: '#0ea5e9',
                color: '#ffffff',
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                textDecoration: 'none',
                fontWeight: 700,
              }}
            >
              查看 Repository
            </a>
            <a
              href="/DEPLOYMENT.md"
              style={{
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                textDecoration: 'none',
                fontWeight: 700,
                border: '1px solid #e2e8f0',
                color: '#0f172a',
                background: '#ffffff',
              }}
            >
              快速部署指南
            </a>
          </div>
        </section>
      </main>
    </>
  );
}
