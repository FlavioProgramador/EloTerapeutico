FROM node:26-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --silent

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
