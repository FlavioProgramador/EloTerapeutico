FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies (only package.json needed for layer caching)
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copy rest of the source code
COPY . .

EXPOSE 3000

# Default command for development
CMD ["npm", "run", "dev"]
