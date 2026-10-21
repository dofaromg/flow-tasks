/**
 * particle-simhash v1.1.0 — SimHash64 語意指紋引擎 (DL580 本地版)
 * 
 * L2-Memory | 64-bit LSH | 中英文分詞
 * 端點: /hash /compare /batch /find-similar /health /
 * 
 * origin_signature: MrLiouWord
 * 怎麼過去就怎麼回來
 */

const VERSION = "1.1.0";

// SimHash64 core algorithm
function simhash64(text) {
  const tokens = tokenize(text);
  const bits = 64;
  const v = new Array(bits).fill(0);

  for (const token of tokens) {
    const hash = fnv1a64(token);
    for (let i = 0; i < bits; i++) {
      if ((hash >> BigInt(i)) & 1n) {
        v[i] += 1;
      } else {
        v[i] -= 1;
      }
    }
  }

  let result = 0n;
  for (let i = 0; i < bits; i++) {
    if (v[i] > 0) {
      result |= (1n << BigInt(i));
    }
  }
  return result;
}

// FNV-1a 64-bit hash
function fnv1a64(str) {
  let hash = 14695981039346656037n;
  const prime = 1099511628211n;
  for (let i = 0; i < str.length; i++) {
    hash ^= BigInt(str.charCodeAt(i));
    hash = (hash * prime) & 0xFFFFFFFFFFFFFFFFn;
  }
  return hash;
}

// Tokenize: handles Chinese + English
function tokenize(text) {
  const tokens = [];
  // Chinese: bigram sliding window
  // English: word split
  const cleaned = text.toLowerCase().trim();
  
  // Split by non-alphanumeric (keeping CJK)
  const segments = cleaned.split(/([a-z0-9]+|[\u4e00-\u9fff\u3400-\u4dbf]+)/g).filter(Boolean);
  
  for (const seg of segments) {
    if (/^[a-z0-9]+$/.test(seg)) {
      // English word
      if (seg.length >= 2) tokens.push(seg);
    } else if (/[\u4e00-\u9fff\u3400-\u4dbf]/.test(seg)) {
      // Chinese: bigrams
      for (let i = 0; i < seg.length - 1; i++) {
        tokens.push(seg.slice(i, i + 2));
      }
      if (seg.length === 1) tokens.push(seg);
    }
  }
  return tokens;
}

// Hamming distance between two 64-bit hashes
function hammingDistance(a, b) {
  let xor = a ^ b;
  let dist = 0;
  while (xor > 0n) {
    dist += Number(xor & 1n);
    xor >>= 1n;
  }
  return dist;
}

// Similarity: 1 - (hamming / 64)
function similarity(a, b) {
  return 1 - hammingDistance(a, b) / 64;
}

// In-memory store for find-similar
const hashStore = new Map();

const json = (data, status = 200) => new Response(JSON.stringify(data, null, 2), {
  status,
  headers: {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "X-Origin-Signature": "MrLiouWord"
  }
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
    }

    // Root
    if (path === "/" || path === "") {
      return json({
        name: "particle-simhash",
        version: VERSION,
        layer: "L2",
        bits: 64,
        description: "SimHash64 語意指紋引擎",
        features: ["64-bit 局部敏感雜湊", "中英文分詞支援", "Hamming Distance 相似度計算", "批量處理", "相似搜尋"],
        endpoints: ["/hash", "/compare", "/batch", "/find-similar"],
        origin_signature: "MrLiouWord",
        runtime: "DL580-local"
      });
    }

    // Health
    if (path === "/health") {
      return json({
        status: "healthy",
        name: "particle-simhash",
        version: VERSION,
        layer: "L2",
        origin_signature: "MrLiouWord",
        stored_hashes: hashStore.size,
        runtime: "DL580-local",
        timestamp: new Date().toISOString()
      });
    }

    // POST /hash — compute simhash for text
    if (path === "/hash" && request.method === "POST") {
      try {
        const body = await request.json();
        const text = body.text || body.content || "";
        if (!text) return json({ success: false, error: "text required" }, 400);

        const hash = simhash64(text);
        const tokens = tokenize(text);

        // Store for find-similar
        const id = body.id || `h_${Date.now()}`;
        hashStore.set(id, { hash, text: text.slice(0, 100), timestamp: Date.now() });

        return json({
          success: true,
          text: text.slice(0, 200),
          simhash: hash.toString(),
          simhash_hex: "0x" + hash.toString(16),
          token_count: tokens.length,
          id,
          origin_signature: "MrLiouWord"
        });
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // POST /compare — compare two texts
    if (path === "/compare" && request.method === "POST") {
      try {
        const body = await request.json();
        const { text1, text2, hash1, hash2 } = body;

        let h1, h2;
        if (hash1 && hash2) {
          h1 = BigInt(hash1);
          h2 = BigInt(hash2);
        } else if (text1 && text2) {
          h1 = simhash64(text1);
          h2 = simhash64(text2);
        } else {
          return json({ success: false, error: "Provide text1+text2 or hash1+hash2" }, 400);
        }

        const dist = hammingDistance(h1, h2);
        const sim = similarity(h1, h2);

        return json({
          success: true,
          hash1: h1.toString(),
          hash2: h2.toString(),
          hamming_distance: dist,
          similarity: Math.round(sim * 10000) / 10000,
          similar: sim >= 0.8,
          origin_signature: "MrLiouWord"
        });
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // POST /batch — hash multiple texts
    if (path === "/batch" && request.method === "POST") {
      try {
        const body = await request.json();
        const texts = body.texts || [];
        if (!Array.isArray(texts)) return json({ success: false, error: "texts[] required" }, 400);

        const results = texts.map((t, i) => {
          const text = typeof t === "string" ? t : t.text || "";
          const hash = simhash64(text);
          return {
            index: i,
            text: text.slice(0, 100),
            simhash: hash.toString(),
            simhash_hex: "0x" + hash.toString(16)
          };
        });

        return json({ success: true, count: results.length, results, origin_signature: "MrLiouWord" });
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // POST /find-similar — find similar texts in store
    if (path === "/find-similar" && request.method === "POST") {
      try {
        const body = await request.json();
        const text = body.text || "";
        const threshold = body.threshold || 0.8;
        const limit = body.limit || 10;

        const queryHash = simhash64(text);
        const results = [];

        for (const [id, entry] of hashStore) {
          const sim = similarity(queryHash, entry.hash);
          if (sim >= threshold) {
            results.push({ id, text: entry.text, similarity: Math.round(sim * 10000) / 10000 });
          }
        }

        results.sort((a, b) => b.similarity - a.similarity);

        return json({
          success: true,
          query_hash: queryHash.toString(),
          threshold,
          found: results.slice(0, limit),
          origin_signature: "MrLiouWord"
        });
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    return json({ error: "route not found", path, endpoints: ["/", "/health", "/hash", "/compare", "/batch", "/find-similar"] }, 404);
  }
};
