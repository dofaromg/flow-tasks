# Particle Edge v4 - API Examples

This document provides example API calls for testing the Particle Edge v4 service.

## Prerequisites

Make sure the service is running:
```bash
npm run dev
```

## Example API Calls

### 1. System Status

```bash
# Get system information
curl http://localhost:8787/

# Health check
curl http://localhost:8787/heartbeat

# Detailed health status
curl http://localhost:8787/health
```

### 2. Particle Management

```bash
# Create a particle (requires authentication)
curl -X POST http://localhost:8787/particles \
  -H "Content-Type: application/json" \
  -H "X-Master-Key: your-master-key" \
  -d '{
    "content": "Test particle data",
    "metadata": {
      "type": "test",
      "priority": "high"
    }
  }'

# Get a particle by ID
curl http://localhost:8787/particles/YOUR_PARTICLE_ID \
  -H "X-Master-Key: your-master-key"

# List all particles
curl http://localhost:8787/particles?limit=10 \
  -H "X-Master-Key: your-master-key"

# Delete a particle
curl -X DELETE http://localhost:8787/particles/YOUR_PARTICLE_ID \
  -H "X-Master-Key: your-master-key"
```

### 3. R2 Storage Operations

```bash
# List R2 objects
curl http://localhost:8787/r2/list?limit=100 \
  -H "X-Master-Key: your-master-key"

# Upload to R2
curl -X PUT http://localhost:8787/r2/test-file.txt \
  -H "X-Master-Key: your-master-key" \
  -H "Content-Type: text/plain" \
  -d "This is test content"
```

### 4. Gate Engine Operations

```bash
# Register with gate
curl -X POST http://localhost:8787/gate/register \
  -H "Content-Type: application/json" \
  -H "X-Master-Key: your-master-key" \
  -d '{}'

# Get gate status
curl -X POST http://localhost:8787/gate/status \
  -H "Content-Type: application/json" \
  -H "X-Master-Key: your-master-key" \
  -d '{}'

# Process data through gate
curl -X POST http://localhost:8787/gate/process \
  -H "Content-Type: application/json" \
  -H "X-Master-Key: your-master-key" \
  -d '{
    "data": "particle data",
    "operation": "transform"
  }'
```

## Response Examples

### Success Response
```json
{
  "success": true,
  "particle_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Particle created successfully"
}
```

### Error Response
```json
{
  "error": "Validation failed",
  "details": [
    {
      "path": ["content"],
      "message": "Required"
    }
  ]
}
```

## Authentication

All endpoints except `/`, `/heartbeat`, `/status`, and `/health` require authentication.

Pass the master key via:
- Header: `X-Master-Key: your-master-key`
- Query parameter: `?key=your-master-key`

## Testing with JavaScript

```javascript
// Create a particle
const response = await fetch('http://localhost:8787/particles', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Master-Key': 'your-master-key',
  },
  body: JSON.stringify({
    content: 'My particle data',
    metadata: { type: 'test' }
  })
});

const data = await response.json();
console.log(data);
```

## Notes

- Replace `your-master-key` with an actual master key
- Replace `YOUR_PARTICLE_ID` with actual particle IDs from create responses
- For production deployment, use the deployed URL instead of `localhost:8787`
