FROM node:24.22.1-alpine
LABEL origin_signature="MrLiouWord"
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY server.js MRL_bridge_route_patch.cjs add_platform_route.cjs mrl_bridge_translation_center.cjs ./
EXPOSE 7800
CMD ["node", "server.js"]
