FROM node:24-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --silent

COPY . .

ARG LIVEKIT_URL=""
ENV LIVEKIT_URL=${LIVEKIT_URL}

RUN npm run build \
    && npm prune --omit=dev

FROM node:24-alpine

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app ./

RUN rm -rf \
        /usr/local/lib/node_modules/npm \
        /usr/local/bin/npm \
        /usr/local/bin/npx \
        /usr/local/lib/node_modules/corepack \
        /usr/local/bin/corepack

EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]