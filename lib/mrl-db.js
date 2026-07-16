let cachedClient = null;

async function getDb() {
  const uri = process.env.MRL_DB_URI;
  if (!uri) return null;

  try {
    if (!cachedClient) {
      const { MongoClient } = await import('mongodb');
      cachedClient = new MongoClient(uri);
      await cachedClient.connect();
    }
    return cachedClient.db('mrl');
  } catch {
    return null;
  }
}

export async function queryRuntimeState() {
  const db = await getDb();
  if (!db) return null;
  return db.collection('runtime_state').findOne({ _id: 'mrl_runtime_v1' });
}

export async function queryProductRegistry() {
  const db = await getDb();
  if (!db) return null;
  return db.collection('product_registry').findOne({ _id: 'mrl_motherbody_v1' });
}

export async function queryModelRegistry() {
  const db = await getDb();
  if (!db) return null;
  return db.collection('model_registry').findOne({ _id: 'mrl_llm_framework_v1' });
}

export async function queryGatewayConnections() {
  const db = await getDb();
  if (!db) return null;
  return db.collection('gateway_connections').find({}).toArray();
}

export async function logConvergence(entry) {
  const db = await getDb();
  if (!db) return null;
  return db.collection('convergence_logs').insertOne({
    ...entry,
    timestamp: new Date(),
  });
}
