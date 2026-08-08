FROM node:24-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN node -e 'const fs = require("fs"); const pkg = JSON.parse(fs.readFileSync("package.json")); pkg.overrides = pkg.overrides || {}; pkg.overrides.nanoid = "3.3.17"; fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2));' \
    && npm install --no-audit --no-fund

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