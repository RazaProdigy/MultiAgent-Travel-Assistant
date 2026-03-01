# MultiAgent Travel Assistant - Frontend
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Install deps (package-lock.json for reproducible builds)
COPY package.json package-lock.json ./
RUN npm ci

# Build-time env: URL the browser will use to reach the API
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
