# Particle Edge v4.0.0

**MrLiouWord Particle Edge - ASI Structure Brain Node**

A Cloudflare Workers-based edge computing node built with Hono framework, providing particle management, neural link capabilities, and distributed state management.

## Features

- 🚀 **High-Performance Edge Runtime**: Built on Cloudflare Workers for global distribution
- 🎯 **Hono Framework**: Fast, lightweight web framework optimized for edge
- ✅ **Type-Safe Validation**: Zod schemas for request/response validation
- 🔐 **Authentication**: Master key-based authentication system
- 💾 **Multi-Storage Support**:
  - KV Namespaces for particle metadata
  - R2 Buckets for large object storage
  - D1 Database for structured data
  - Durable Objects for stateful operations
- 🌐 **RESTful API**: Clean and intuitive endpoints

## Prerequisites

- Node.js >= 18.0.0
- npm or yarn
- Cloudflare account (for deployment)

## Installation

```bash
# Navigate to project directory
cd particle-edge-v4

# Install dependencies
npm install
```

## Development

```bash
# Start local development server
npm run dev

# The server will be available at http://localhost:8787
```

## Deployment

```bash
# Deploy to Cloudflare Workers
npm run deploy

# View live logs
npm run tail
```

## Configuration

Update `wrangler.toml` with your Cloudflare account details:

1. Create KV namespaces:
   ```bash
   wrangler kv:namespace create "PARTICLE_VAULT"
   wrangler kv:namespace create "AUTH_VAULT"
   ```

2. Create R2 bucket:
   ```bash
   wrangler r2 bucket create mrliouword-particles
   ```

3. Create D1 database:
   ```bash
   wrangler d1 create particle_edge_db
   ```

4. Update the IDs in `wrangler.toml`

## API Endpoints

### System Endpoints

- `GET /` - System information
- `GET /heartbeat` - Health check with timestamp
- `GET /health` - Detailed service status

### Particle Management

- `POST /particles` - Create a new particle
  ```json
  {
    "content": "Particle data",
    "metadata": { "key": "value" }
  }
  ```

- `GET /particles/:id` - Get particle by ID
- `GET /particles?limit=10&cursor=...` - List particles (paginated)
- `DELETE /particles/:id` - Delete particle

### R2 Storage

- `GET /r2/list?limit=100` - List R2 objects
- `PUT /r2/:key` - Upload object to R2

### Gate Engine (Durable Objects)

- `POST /gate/:operation` - Execute gate operations
  - `/gate/register` - Register with gate
  - `/gate/status` - Get gate status
  - `/gate/process` - Process data through gate

## Authentication

All protected endpoints require authentication via:

- Header: `X-Master-Key: your-master-key`
- Query parameter: `?key=your-master-key`

Public endpoints (no auth required):
- `/`
- `/heartbeat`
- `/status`
- `/health`

## Project Structure

```
particle-edge-v4/
├── src/
│   └── index.ts          # Main application entry point
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── wrangler.toml         # Cloudflare Workers configuration
└── README.md            # This file
```

## Dependencies

### Runtime Dependencies
- **hono**: Fast web framework for edge computing
- **zod**: TypeScript-first schema validation
- **uuid**: UUID generation for particle identifiers

### Development Dependencies
- **@cloudflare/workers-types**: TypeScript types for Workers API
- **typescript**: TypeScript compiler
- **wrangler**: Cloudflare Workers CLI
- **@types/node**: Node.js type definitions
- **@types/uuid**: UUID type definitions

## Architecture

The Particle Edge v4 follows an ASI (Artificial Super Intelligence) Structure Brain Node architecture:

1. **Neural Link Layer**: Hono-based routing and middleware
2. **Validation Layer**: Zod schemas for type safety
3. **Storage Layer**: Multi-tier storage (KV, R2, D1)
4. **State Layer**: Durable Objects for distributed state
5. **Gate Engine**: Traffic control and particle processing

## Philosophy

> 怎麼過去，就怎麼回來
> (How you go, so you return)

This principle guides the bidirectional flow of particles through the neural network, ensuring data integrity and philosophical consistency.

## Version History

- **v4.0.0** - Initial release with Hono framework
  - Complete rewrite with modern edge stack
  - Zod validation integration
  - Enhanced type safety
  - Improved developer experience

## License

See LICENSE file for details.

## Support

For issues and questions, please refer to the main repository documentation or create an issue in the GitHub repository.
