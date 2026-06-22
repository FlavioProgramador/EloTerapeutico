FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies (only package.json needed for layer caching)
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copy rest of the source code
COPY . .

# Build the Next.js app (optional for production)
# RUN npm run build

EXPOSE 3000

# Default command for development
CMD ["npm", "run", "dev"]
