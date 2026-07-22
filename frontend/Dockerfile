FROM node:24-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --silent

COPY . .

ARG LIVEKIT_URL=""
ENV LIVEKIT_URL=${LIVEKIT_URL}

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
