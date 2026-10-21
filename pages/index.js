import Head from 'next/head';
import { useEffect, useState } from 'react';
import { getGrowthBook, isFeatureOn, getFeatureValue, FLAGS } from '../lib/growthbook';

const features = [
  '🧠 MRLiou 粒子語言核心 - 邏輯種子運算',
  '💾 記憶封存系統 - 完整狀態保存',
  '🔄 函數鏈執行 - STRUCTURE → MARK → FLOW',
  '🐳 Docker 本地開發 - 私人環境部署',
  '📊 私人觀測工具 - 本地監控與記錄',
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
        <title>MRLiou 粒子語言系統 - 私人開發環境</title>
        <meta
          name="description"
          content="MRLiou Particle Language Core System - 私人開發與觀測環境。© Mr.liou - All Rights Reserved"
        />
        <meta property="og:title" content="MRLiou 粒子語言系統" />
        <meta property="og:description" content="© Mr.liou 私人開發專案" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="author" content="MRLiou / Mr.liou" />
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
          style={{
            maxWidth: 720,
            width: '100%',
            background: '#ffffff',
            borderRadius: 16,
            boxShadow: '0 16px 48px rgba(15, 23, 42, 0.08)',
            padding: '2.5rem',
            border: '1px solid #e2e8f0',
            marginTop: getContentMarginTop(),
          }}
        >
          <p style={{ color: '#64748b', fontWeight: 600, letterSpacing: 1.2, marginBottom: 12 }}>
            🔒 MRLIOU 私人開發環境
          </p>
          <h1 style={{ fontSize: '2.5rem', margin: '0 0 1rem', lineHeight: 1.2 }}>
            MRLiou 粒子語言核心系統
          </h1>
          <p style={{ color: '#475569', marginBottom: '1.5rem', fontSize: '1.05rem', lineHeight: 1.7 }}>
            © 2025 Mr.liou - All Rights Reserved<br/>
            私人開發與觀測環境 | Particle Language Core System<br/>
            不對外公開 | Private Development Only
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
              href="/PRIVATE_DEVELOPMENT.md"
              style={{
                background: colorMap[checkoutColor] || colorMap.blue,
                color: '#ffffff',
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                textDecoration: 'none',
                fontWeight: 700,
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              🔒 私人開發指南
            </a>
            <a
              href="/particle_core"
              style={{
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                textDecoration: 'none',
                fontWeight: 700,
                border: '1px solid #e2e8f0',
                color: '#0f172a',
                background: '#ffffff',
                transition: 'box-shadow 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)')}
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = 'none')}
            >
              🧠 粒子語言核心
            </a>
            <a
              href="mailto:z814241@gmail.com"
              style={{
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                textDecoration: 'none',
                fontWeight: 700,
                border: '1px solid #e2e8f0',
                color: '#0f172a',
                background: '#ffffff',
                transition: 'box-shadow 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)')}
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = 'none')}
            >
              📧 聯絡 MRLiou
            </a>
          </div>

          {/* Brand and Copyright Info */}
          <div
            style={{
              marginTop: '2rem',
              padding: '1rem',
              background: '#f1f5f9',
              borderRadius: 8,
              fontSize: '0.875rem',
              color: '#475569',
              textAlign: 'center',
            }}
          >
            <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
              🏢 MRLiou 品牌 | Mr.liou
            </p>
            <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
              © 2025 Mr.liou - All Rights Reserved<br/>
              私人開發環境 | 不對外公開<br/>
              Particle Language Core System
            </p>
          </div>
        </section>
      </main>
    </>
  );
}
