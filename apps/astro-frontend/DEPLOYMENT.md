# Astro Frontend Deployment Summary

## Overview

This document describes the Astro frontend application added to the FlowAgent GKE Starter project.

## What is Astro?

[Astro](https://astro.build) is a modern static site generator that focuses on performance by shipping zero JavaScript by default. It's ideal for content-focused websites and offers excellent developer experience with component-based architecture.

## Implementation Details

### Project Location
- **Path**: `apps/astro-frontend/`
- **Built with**: Astro v4.16.19
- **Server**: nginx (Alpine Linux)

### Key Features
- ⚡ **Static Site Generation**: Pre-renders all pages at build time
- 🎨 **Component-based**: Uses `.astro` components with scoped styles
- 📦 **Minimal Dependencies**: Clean, lightweight setup
- 🚀 **Fast Performance**: Optimized static assets with nginx caching
- 🔒 **Security Headers**: Configured nginx with security best practices

### Development Commands

```bash
# Navigate to project
cd apps/astro-frontend

# Install dependencies
npm install

# Start development server (http://localhost:4321)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Production Deployment

#### Docker Build
The application uses a multi-stage Docker build:
1. **deps stage**: Install Node.js dependencies
2. **builder stage**: Build the static site
3. **runner stage**: Serve with nginx on Alpine Linux

```bash
# Build Docker image
docker build -t astro-frontend:latest apps/astro-frontend/

# Run locally
docker run -p 8080:80 astro-frontend:latest
```

#### Kubernetes Deployment

**Resources Created:**
- Deployment: `astro-frontend` (2 replicas)
- Service: `astro-frontend` (LoadBalancer type)

**Resource Limits:**
- Memory: 64Mi request, 128Mi limit
- CPU: 100m request, 200m limit

**Deployment Command:**
```bash
# Deploy to GKE
kubectl apply -k apps/astro-frontend/

# Check status
kubectl get pods -n flowagent -l app=astro-frontend
kubectl get svc -n flowagent astro-frontend
```

**Access the Service:**
```bash
# Get external IP
kubectl get svc astro-frontend -n flowagent

# Visit http://<EXTERNAL-IP>/
```

## Project Structure

```
apps/astro-frontend/
├── .astro/              # Astro build cache
├── .gitignore          # Git ignore patterns
├── Dockerfile          # Multi-stage Docker build
├── README.md           # Project documentation
├── astro.config.mjs    # Astro configuration
├── deployment.yaml     # Kubernetes manifests
├── dist/               # Built static files (ignored in git)
├── kustomization.yaml  # Kustomize config
├── nginx.conf          # nginx server configuration
├── node_modules/       # Dependencies (ignored in git)
├── package.json        # Node.js dependencies
├── package-lock.json   # Locked dependencies
├── public/             # Static assets
│   └── favicon.svg
├── src/
│   ├── env.d.ts       # TypeScript environment types
│   ├── layouts/       # Layout components
│   │   └── Layout.astro
│   └── pages/         # Page routes
│       └── index.astro
└── tsconfig.json      # TypeScript configuration
```

## Integration with FlowAgent

The Astro frontend integrates with the FlowAgent ecosystem:

1. **Kubernetes Deployment**: Deployed alongside other microservices in the `flowagent` namespace
2. **LoadBalancer Service**: Exposed via GCP LoadBalancer for external access
3. **Container Registry**: Image stored at `asia-east1-docker.pkg.dev/flowmemorysync/flowagent/astro-frontend:latest`

## Comparison with Next.js Frontend

| Feature | Next.js Frontend | Astro Frontend |
|---------|------------------|----------------|
| **Type** | SSR/SSG React App | Pure Static Site |
| **Runtime** | Node.js | nginx |
| **Port** | 3000 | 80 |
| **Memory** | 256Mi-512Mi | 64Mi-128Mi |
| **CPU** | 200m-500m | 100m-200m |
| **Use Case** | Dynamic apps, APIs | Static content, docs |
| **Build Time** | ~30-60s | ~5-10s |

## When to Use Each Frontend

### Use Astro Frontend When:
- Building static content sites
- Maximum performance is critical
- Minimal resource usage is needed
- No server-side rendering required
- Building documentation or marketing pages

### Use Next.js Frontend When:
- Need server-side rendering
- Building dynamic applications
- Require API routes
- Need authentication flows
- Complex state management

## nginx Configuration

The Astro frontend uses nginx with:
- **Gzip compression** for faster load times
- **Cache headers** for static assets (1 year)
- **Security headers** (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- **Single-page app routing** with fallback to index.html

## CI/CD Integration

To integrate with CI/CD pipelines:

1. **Build Docker Image**:
   ```bash
   docker build -t asia-east1-docker.pkg.dev/flowmemorysync/flowagent/astro-frontend:$TAG apps/astro-frontend/
   ```

2. **Push to Registry**:
   ```bash
   docker push asia-east1-docker.pkg.dev/flowmemorysync/flowagent/astro-frontend:$TAG
   ```

3. **Update Deployment**:
   ```bash
   kubectl set image deployment/astro-frontend astro=asia-east1-docker.pkg.dev/flowmemorysync/flowagent/astro-frontend:$TAG -n flowagent
   ```

## Troubleshooting

### Build Issues
```bash
# Clean and rebuild
cd apps/astro-frontend
rm -rf node_modules dist .astro
npm install
npm run build
```

### Container Issues
```bash
# Check logs
kubectl logs -f deployment/astro-frontend -n flowagent

# Check pod status
kubectl describe pod -l app=astro-frontend -n flowagent
```

### Access Issues
```bash
# Check service
kubectl get svc astro-frontend -n flowagent

# Port forward for testing
kubectl port-forward svc/astro-frontend 8080:80 -n flowagent
# Visit http://localhost:8080
```

## Future Enhancements

Potential improvements for the Astro frontend:

1. **Content Collections**: Add markdown-based content management
2. **Integrations**: Add React/Vue/Svelte islands for interactive components
3. **SEO**: Implement sitemap generation and meta tags
4. **Analytics**: Integrate with analytics platforms
5. **i18n**: Add internationalization support
6. **CDN**: Integrate with GCP Cloud CDN for global distribution

## Resources

- [Astro Documentation](https://docs.astro.build)
- [Astro GitHub](https://github.com/withastro/astro)
- [Astro Discord](https://astro.build/chat)
- [FlowAgent Main README](../../README.md)
- [Apps Deployment Guide](../README.md)

---

**Created**: 2026-02-04  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
