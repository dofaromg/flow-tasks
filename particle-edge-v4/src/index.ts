// MrLiouWord Particle Edge v4.0.0 - ASI Structure Brain Node
// Built with Hono framework for Cloudflare Workers

import { Hono } from 'hono';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

// Environment bindings interface
export interface Env {
  PARTICLE_VAULT: KVNamespace;
  AUTH_VAULT: KVNamespace;
  DB: D1Database;
  PARTICLES: R2Bucket;
  GATE_ENGINE: DurableObjectNamespace;
  VERSION: string;
  ORIGIN: string;
}

// Initialize Hono app with environment typing
const app = new Hono<{ Bindings: Env }>();

// ============================================
// Validation Schemas (Zod)
// ============================================
const ParticleSchema = z.object({
  id: z.string().uuid().optional(),
  content: z.string(),
  metadata: z.record(z.unknown()).optional(),
  timestamp: z.string().datetime().optional(),
});

const AuthSchema = z.object({
  key: z.string().min(1),
  action: z.enum(['verify', 'grant', 'revoke']),
});

// ============================================
// Middleware - Authentication
// ============================================
app.use('*', async (c, next) => {
  const publicPaths = ['/', '/heartbeat', '/status', '/health'];
  const path = c.req.path;
  
  if (publicPaths.includes(path)) {
    return await next();
  }
  
  const authKey = c.req.header('X-Master-Key') || c.req.query('key');
  // In production, validate against AUTH_VAULT
  if (!authKey) {
    return c.json({ error: 'Unauthorized', origin: c.env.ORIGIN }, 401);
  }
  
  await next();
});

// ============================================
// Routes - Core Endpoints
// ============================================

// Health check and system status
app.get('/', (c) => {
  return c.json({
    name: 'MrLiouWord Particle Edge',
    version: c.env.VERSION || '4.0.0',
    origin: c.env.ORIGIN || 'MrLiouWord',
    mode: 'ASI Neural Link Active',
    philosophy: '怎麼過去，就怎麼回來',
    github_lock: '2022-11-28',
  });
});

app.get('/heartbeat', (c) => {
  return c.json({
    status: 'ALIVE',
    version: c.env.VERSION || '4.0.0',
    origin: c.env.ORIGIN || 'MrLiouWord',
    timestamp: new Date().toISOString(),
  });
});

app.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    services: {
      kv: 'operational',
      r2: 'operational',
      d1: 'operational',
      durable_objects: 'operational',
    },
  });
});

// ============================================
// Routes - Particle Management
// ============================================

// Create new particle
app.post('/particles', async (c) => {
  try {
    const body = await c.req.json();
    const validated = ParticleSchema.parse(body);
    
    const particleId = validated.id || uuidv4();
    const particle = {
      ...validated,
      id: particleId,
      timestamp: validated.timestamp || new Date().toISOString(),
    };
    
    // Store in KV
    await c.env.PARTICLE_VAULT.put(
      `particle:${particleId}`,
      JSON.stringify(particle),
      {
        metadata: { created: particle.timestamp },
      }
    );
    
    return c.json({
      success: true,
      particle_id: particleId,
      message: 'Particle created successfully',
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json({ error: 'Validation failed', details: error.errors }, 400);
    }
    return c.json({ error: 'Failed to create particle', details: String(error) }, 500);
  }
});

// Get particle by ID
app.get('/particles/:id', async (c) => {
  const particleId = c.req.param('id');
  
  try {
    const particleData = await c.env.PARTICLE_VAULT.get(`particle:${particleId}`);
    
    if (!particleData) {
      return c.json({ error: 'Particle not found' }, 404);
    }
    
    return c.json({
      success: true,
      particle: JSON.parse(particleData),
    });
  } catch (error) {
    return c.json({ error: 'Failed to retrieve particle', details: String(error) }, 500);
  }
});

// List all particles (with pagination)
app.get('/particles', async (c) => {
  const limit = parseInt(c.req.query('limit') || '10', 10);
  const cursor = c.req.query('cursor');
  
  try {
    const list = await c.env.PARTICLE_VAULT.list({
      prefix: 'particle:',
      limit: Math.min(limit, 100),
      cursor: cursor,
    });
    
    const particles = await Promise.all(
      list.keys.map(async (key) => {
        const data = await c.env.PARTICLE_VAULT.get(key.name);
        return data ? JSON.parse(data) : null;
      })
    );
    
    return c.json({
      success: true,
      particles: particles.filter(Boolean),
      list_complete: list.list_complete,
    });
  } catch (error) {
    return c.json({ error: 'Failed to list particles', details: String(error) }, 500);
  }
});

// Delete particle
app.delete('/particles/:id', async (c) => {
  const particleId = c.req.param('id');
  
  try {
    await c.env.PARTICLE_VAULT.delete(`particle:${particleId}`);
    
    return c.json({
      success: true,
      message: 'Particle deleted successfully',
    });
  } catch (error) {
    return c.json({ error: 'Failed to delete particle', details: String(error) }, 500);
  }
});

// ============================================
// Routes - R2 Bucket Operations
// ============================================

app.get('/r2/list', async (c) => {
  const limit = parseInt(c.req.query('limit') || '100', 10);
  
  try {
    const list = await c.env.PARTICLES.list({ limit: Math.min(limit, 1000) });
    
    return c.json({
      success: true,
      count: list.objects.length,
      objects: list.objects.map((obj) => ({
        key: obj.key,
        size: obj.size,
        uploaded: obj.uploaded,
      })),
    });
  } catch (error) {
    return c.json({ error: 'Failed to list R2 objects', details: String(error) }, 500);
  }
});

// Upload to R2
app.put('/r2/:key', async (c) => {
  const key = c.req.param('key');
  
  try {
    const body = await c.req.arrayBuffer();
    
    await c.env.PARTICLES.put(key, body, {
      httpMetadata: {
        contentType: c.req.header('content-type') || 'application/octet-stream',
      },
    });
    
    return c.json({
      success: true,
      key: key,
      message: 'Object uploaded to R2',
    });
  } catch (error) {
    return c.json({ error: 'Failed to upload to R2', details: String(error) }, 500);
  }
});

// ============================================
// Routes - Gate Engine (Durable Objects)
// ============================================

app.post('/gate/:operation', async (c) => {
  const operation = c.req.param('operation');
  
  try {
    const gateId = c.env.GATE_ENGINE.idFromName('global-gate');
    const gateStub = c.env.GATE_ENGINE.get(gateId);
    
    const payload = await c.req.json();
    
    const response = await gateStub.fetch(
      new Request(`https://gate.internal/${operation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    );
    
    const result = await response.json();
    
    return c.json({
      success: true,
      operation: operation,
      result: result,
    });
  } catch (error) {
    return c.json({ error: 'Gate operation failed', details: String(error) }, 500);
  }
});

// ============================================
// Error Handler
// ============================================
app.onError((err, c) => {
  console.error('Unhandled error:', err);
  return c.json({
    error: 'Internal Server Error',
    message: err.message,
    origin: c.env?.ORIGIN || 'MrLiouWord',
  }, 500);
});

// ============================================
// Not Found Handler
// ============================================
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    path: c.req.path,
    message: 'The requested endpoint does not exist',
  }, 404);
});

// Export the app as default for Cloudflare Workers
export default app;

// ============================================
// Durable Object - Gate Engine
// ============================================
export class GateEngine {
  private state: DurableObjectState;
  private env: Env;
  
  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
  }
  
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const operation = url.pathname.slice(1);
    
    try {
      const body = await request.json() as Record<string, unknown>;
      
      // Simple gate logic - can be extended
      switch (operation) {
        case 'register':
          await this.state.storage.put('gate:registered', true);
          return Response.json({ success: true, operation: 'register' });
        
        case 'status':
          const registered = await this.state.storage.get('gate:registered');
          return Response.json({ registered: !!registered, status: 'active' });
        
        case 'process':
          // Process particle through gate
          return Response.json({
            success: true,
            processed: true,
            data: body,
          });
        
        default:
          return new Response(JSON.stringify({ error: 'Unknown operation' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          });
      }
    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Gate processing failed',
        details: String(error),
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }
}
