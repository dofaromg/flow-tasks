'use strict';
// Session or verified user record ownership; no DB mutation.
// origin_signature: MrLiouWord
function ownsAnalysis(record, sessionId, userId) {
  if (!record) return false;
  if (userId && record.user_id && record.user_id === userId) return true;
  return !!(sessionId && record.session_id && record.session_id === sessionId);
}
function ownsOrder(record, sessionId, userId) {
  return ownsAnalysis(record, sessionId, userId);
}
module.exports = { ownsAnalysis, ownsOrder };
