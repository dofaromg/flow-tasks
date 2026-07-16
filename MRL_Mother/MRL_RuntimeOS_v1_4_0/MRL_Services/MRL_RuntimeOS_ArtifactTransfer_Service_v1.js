const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class MRLRuntimeOSArtifactTransferService {
  constructor(root) {
    this.root = root;
    this.origin_signature = 'MrLiouWord';
    this.sessions = new Map();
  }
  begin({ artifact_id, filename, total_chunks, content_type = 'application/octet-stream' }) {
    const id = artifact_id || `MRL_ARTIFACT_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    const session = { artifact_id: id, filename: filename || id, total_chunks: Number(total_chunks || 1), content_type, chunks: new Map(), created_at: new Date().toISOString() };
    this.sessions.set(id, session);
    return { origin_signature: this.origin_signature, ...session, chunks: 0 };
  }
  addChunk({ artifact_id, chunk_index, data_base64 }) {
    const session = this.sessions.get(artifact_id);
    if (!session) throw new Error('MRL_ARTIFACT_SESSION_NOT_FOUND');
    const data = Buffer.from(data_base64 || '', 'base64');
    session.chunks.set(Number(chunk_index), data);
    return { origin_signature: this.origin_signature, artifact_id, received: session.chunks.size, total_chunks: session.total_chunks, complete: session.chunks.size === session.total_chunks };
  }
  assemble({ artifact_id }) {
    const session = this.sessions.get(artifact_id);
    if (!session) throw new Error('MRL_ARTIFACT_SESSION_NOT_FOUND');
    if (session.chunks.size !== session.total_chunks) throw new Error('MRL_ARTIFACT_INCOMPLETE');
    const buffers = [];
    for (let i = 0; i < session.total_chunks; i++) {
      if (!session.chunks.has(i)) throw new Error(`MRL_ARTIFACT_MISSING_CHUNK:${i}`);
      buffers.push(session.chunks.get(i));
    }
    const data = Buffer.concat(buffers);
    const dir = path.join(this.root, 'MRL_Storage', 'MRL_Artifacts');
    fs.mkdirSync(dir, { recursive: true });
    const safe = session.filename.replace(/[^A-Za-z0-9_.-]/g, '_');
    const filePath = path.join(dir, safe);
    fs.writeFileSync(filePath, data);
    const sha256 = crypto.createHash('sha256').update(data).digest('hex');
    const rec = { origin_signature: this.origin_signature, artifact_id, filename: session.filename, path: filePath, size: data.length, sha256, assembled_at: new Date().toISOString() };
    fs.writeFileSync(path.join(dir, `${safe}.mrl.json`), JSON.stringify(rec, null, 2));
    this.sessions.delete(artifact_id);
    return rec;
  }
}

module.exports = { MRLRuntimeOSArtifactTransferService };
