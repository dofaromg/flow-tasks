import { SpeedInsights } from '@vercel/speed-insights/next';

function App({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <SpeedInsights />
    </>
  );
}

export default App;
