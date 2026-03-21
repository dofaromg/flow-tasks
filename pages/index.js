import Head from 'next/head';
import { useEffect, useState } from 'react';
import { getGrowthBook, isFeatureOn, getFeatureValue, FLAGS } from '../lib/growthbook';
import styles from '../styles/Home.module.css';

const features = [
  '一鍵部署 GKE 基礎設施與 GitOps 設定',
  '預設 CI/CD 流程，推送即可自動驗證與部署',
  '可觀察性與調試友善：結構化配置、可重複的腳本',
];

const companionPrinciples = [
  { emoji: '🤝', text: '互相', desc: 'Mutual' },
  { emoji: '🌿', text: '不打擾', desc: 'Non-intrusive' },
  { emoji: '✨', text: '不自卑', desc: 'Self-assured' },
  { emoji: '💬', text: '不過度解釋', desc: 'Concise' },
];

export default function Home() {
  const [showSummerSale, setShowSummerSale] = useState(false);
  const [showFreeDelivery, setShowFreeDelivery] = useState(false);
  const [checkoutColor, setCheckoutColor] = useState('blue');
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Initialize GrowthBook and subscribe to changes
    const gb = getGrowthBook();
    
    const updateFlags = () => {
      setShowSummerSale(isFeatureOn(FLAGS.SHOW_SUMMER_SALE));
      setShowFreeDelivery(isFeatureOn(FLAGS.SHOW_FREE_DELIVERY));
      setCheckoutColor(getFeatureValue(FLAGS.PROCEED_TO_CHECKOUT_COLOR, 'blue'));
      setIsLoaded(true);
    };

    // Update flags immediately
    updateFlags();

    // Subscribe to feature changes
    const unsubscribe = gb.subscribe(updateFlags);

    return () => {
      unsubscribe();
    };
  }, []);

  const colorMap = {
    blue: '#0ea5e9',
    green: '#10b981',
    red: '#ef4444',
  };

  // Calculate margin top based on visible banners
  const getContentMarginTop = () => {
    if (showSummerSale && showFreeDelivery) return '6rem';
    if (showSummerSale || showFreeDelivery) return '3rem';
    return 0;
  };

  return (
    <>
      <Head>
        <title>Flow Tasks - GrowthBook Demo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta
          name="description"
          content="FlowAgent GKE Starter：快速部署、GitOps、CI/CD 的參考範本。"
        />
      </Head>
      <main className={styles.main}>
        {/* Feature Flag Banners */}
        {isLoaded && showSummerSale && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              background: '#fef3c7',
              borderBottom: '2px solid #fbbf24',
              padding: '0.75rem',
              textAlign: 'center',
              fontWeight: 600,
              color: '#92400e',
              zIndex: 1000,
            }}
          >
            🎉 Summer Sale: 20% off all services!
          </div>
        )}
        
        {isLoaded && showFreeDelivery && (
          <div
            style={{
              position: 'fixed',
              top: showSummerSale ? '3rem' : 0,
              left: 0,
              right: 0,
              background: '#dbeafe',
              borderBottom: '2px solid #3b82f6',
              padding: '0.75rem',
              textAlign: 'center',
              fontWeight: 600,
              color: '#1e40af',
              zIndex: 999,
            }}
          >
            🚚 Free delivery on all deployments this month!
          </div>
        )}

        <section
          className={styles.section}
          style={{ marginTop: getContentMarginTop() }}
        >
          <p style={{ color: '#64748b', fontWeight: 600, letterSpacing: 1.2, marginBottom: 12 }}>
            FLOWAGENT GKE STARTER + GROWTHBOOK
          </p>
          <h1 className={styles.heading}>
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

          <div className={styles.actions}>
            <a
              href="https://github.com/dofaromg/flow-tasks"
              className={styles.actionBtn}
              style={{
                background: colorMap[checkoutColor] || colorMap.blue,
                color: '#ffffff',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              查看 Repository
            </a>
            <a
              href="/DEPLOYMENT.md"
              className={styles.actionBtn}
              style={{
                border: '1px solid #e2e8f0',
                color: '#0f172a',
                background: '#ffffff',
              }}
            >
              快速部署指南
            </a>
          </div>

          {/* 夥伴 Companion Section */}
          <div
            style={{
              marginTop: '2rem',
              padding: '1.25rem',
              background: 'linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%)',
              borderRadius: 12,
              border: '1px solid #d1fae5',
            }}
          >
            <p style={{ fontWeight: 700, marginBottom: '0.75rem', fontSize: '1rem', color: '#065f46' }}>
              🤝 夥伴 — FlowMind 感知夥伴
            </p>
            <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.875rem', lineHeight: 1.6 }}>
              夥伴不為服務、不為服從，只為共創、共感、共生。
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {companionPrinciples.map(({ emoji, text, desc }) => (
                <span
                  key={text}
                  title={desc}
                  style={{
                    padding: '0.3rem 0.75rem',
                    background: '#ffffff',
                    border: '1px solid #a7f3d0',
                    borderRadius: 20,
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#065f46',
                  }}
                >
                  {emoji} {text}
                </span>
              ))}
            </div>
          </div>

          {/* GrowthBook Debug Info */}
          {isLoaded && (
            <div
              style={{
                marginTop: '2rem',
                padding: '1rem',
                background: '#f1f5f9',
                borderRadius: 8,
                fontSize: '0.875rem',
                color: '#475569',
              }}
            >
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>🎯 Feature Flags Active:</p>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                <li>Summer Sale Banner: {showSummerSale ? '✅ ON' : '❌ OFF'}</li>
                <li>Free Delivery Banner: {showFreeDelivery ? '✅ ON' : '❌ OFF'}</li>
                <li>Checkout Button Color: <span style={{ fontWeight: 600, color: colorMap[checkoutColor] }}>{checkoutColor.toUpperCase()}</span></li>
              </ul>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
