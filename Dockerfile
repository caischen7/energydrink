# Two-stage build for the ION_INTEL site (landing page + market-intelligence
# dashboard). Mirrors the Cloud Run deployment pattern used by the
# msbai-dwd-csc9720 dashboard: build server-side, serve a container that
# listens on $PORT.

# ---- Stage 1: build the static site with Vite ----
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Stage 2: serve the static build with nginx ----
FROM nginx:1.27-alpine
# Cloud Run injects $PORT (default 8080). The official nginx image renders
# /etc/nginx/templates/*.template through envsubst at container start, so the
# server block picks up the right port automatically.
ENV PORT=8080
COPY deploy/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
# nginx:alpine's default entrypoint renders templates then launches nginx.
