FROM node:24-alpine AS builder

WORKDIR /app

RUN apk upgrade --no-cache

COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund \
    && npm install nanoid@^3.3.18 --no-save

COPY . .

ARG LIVEKIT_URL=""
ENV LIVEKIT_URL=${LIVEKIT_URL}

RUN npm run build \
    && npm prune --omit=dev

FROM node:24-alpine

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

RUN apk upgrade --no-cache

COPY --from=builder /app ./

RUN rm -rf \
        /usr/local/lib/node_modules/npm \
        /usr/local/bin/npm \
        /usr/local/bin/npx \
        /usr/local/lib/node_modules/corepack \
        /usr/local/bin/corepack

EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]