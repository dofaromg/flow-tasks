const canonicalPagesOrigins = new Set([
  'https://flow-tasks.pages.dev',
  'https://mrliouword.com',
  'https://www.mrliouword.com',
]);

export function isAllowedOrigin(origin, configuredOrigins = '') {
  if (!origin) return false;
  const configured = configuredOrigins.split(',').map((value) => value.trim()).filter(Boolean);
  return canonicalPagesOrigins.has(origin) || configured.includes(origin);
}

export function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Accept, Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}
