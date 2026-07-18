# ION — Liquid Hardware → Google Cloud Run
# Multi-stage: build the static Vite site, then serve it with nginx on $PORT.

# ---------- build ----------
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---------- serve ----------
FROM nginx:1.27-alpine
# Cloud Run injects $PORT (default 8080). The nginx image runs envsubst on
# /etc/nginx/templates/*.template at startup; NGINX_ENVSUBST_FILTER=PORT keeps
# it from touching nginx's own runtime variables ($uri, $host, ...).
ENV PORT=8080
ENV NGINX_ENVSUBST_FILTER=PORT
COPY nginx.conf /etc/nginx/templates/default.conf.template
# Basic Auth credentials for the guarded locations (see nginx.conf):
# .htpasswd → /data/dashboard.json (Market Intel), .htpasswd-admin → /admin/ (Site Scout)
COPY .htpasswd /etc/nginx/.htpasswd
COPY .htpasswd-admin /etc/nginx/.htpasswd-admin
COPY --from=build /app/dist /usr/share/nginx/html
