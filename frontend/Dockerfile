FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

EXPOSE 5173

# Vite dev server — bind on all interfaces for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
