# ── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cache)
COPY package*.json ./
RUN npm ci

# Copy source and build for production
COPY . .
RUN npm run build -- --configuration production

# ── Stage 2: Serve ───────────────────────────────────────────────────────────
FROM nginx:alpine

# Replace default nginx config with our SPA-aware config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled Angular app from builder stage
COPY --from=builder /app/dist/ai-chat-frontend/browser /usr/share/nginx/html

EXPOSE 80
