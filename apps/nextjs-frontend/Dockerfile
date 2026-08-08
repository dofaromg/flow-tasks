# Multi-stage build for Next.js application
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables
ARG NEXT_PUBLIC_GROWTHBOOK_API_HOST
ARG NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY
ENV NEXT_PUBLIC_GROWTHBOOK_API_HOST=$NEXT_PUBLIC_GROWTHBOOK_API_HOST
ENV NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=$NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY

# Build Next.js app
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Add non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set proper permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Start Next.js server
CMD ["node", "server.js"]
