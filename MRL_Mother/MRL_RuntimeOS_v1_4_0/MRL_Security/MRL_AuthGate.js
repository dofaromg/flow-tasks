function MRL_authRequired() { return String(process.env.MRL_AUTH_REQUIRED || 'false').toLowerCase() === 'true'; }
function MRL_validateAuth(req) {
  if (!MRL_authRequired()) return { ok:true, mode:'disabled' };
  const expected = process.env.MRL_API_TOKEN || '';
  const got = (req.headers['authorization'] || '').replace(/^Bearer\s+/i,'') || req.headers['x-mrl-token'] || '';
  if (!expected) return { ok:false, code:500, error:'MRL_AUTH_TOKEN_NOT_CONFIGURED' };
  if (got !== expected) return { ok:false, code:401, error:'MRL_AUTH_FAILED' };
  return { ok:true, mode:'token' };
}
module.exports = { MRL_authRequired, MRL_validateAuth };
