import './globals.css';

export const metadata = {
  title: 'MRLiou Control Plane',
  description: 'MRLiou 前端控制平面 — © Mr.liou',
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}
