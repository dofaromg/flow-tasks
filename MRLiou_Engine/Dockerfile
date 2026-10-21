# MRL ASI Particle Engine — DL580 G9
# origin_signature: MrLiouWord

FROM node:22-alpine

WORKDIR /app

# Dependencies first (cache layer)
COPY package.json ./
RUN npm install --production

# Application code
COPY server.js worker-adapter.js ./
COPY workers/ ./workers/
COPY config/ ./config/

EXPOSE 7700

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD wget -q -O- http://localhost:7700/health || exit 1

CMD ["node", "server.js"]
