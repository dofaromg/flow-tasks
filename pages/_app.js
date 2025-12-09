import { useEffect } from 'react';
import { injectSpeedInsights } from '@vercel/speed-insights';

function App({ Component, pageProps }) {
  useEffect(() => {
    injectSpeedInsights();
  }, []);

  return <Component {...pageProps} />;
}

export default App;
