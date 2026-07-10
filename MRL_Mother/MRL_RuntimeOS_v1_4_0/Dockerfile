FROM node:20-bookworm-slim
WORKDIR /app
COPY . .
RUN npm install --omit=dev
ENV MRL_PORT=8788 MRL_HOST=0.0.0.0 MRL_AUTH_REQUIRED=false
EXPOSE 8788
CMD ["node", "MRL_API/MRL_RuntimeServer.js"]
