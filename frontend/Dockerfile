# MediSecure frontend — Node 24 build + unprivileged Nginx runtime
# Node >=24.15 satisfies dependency engines (^22.22.2 || ^24.15.0 || >=26).
FROM node:24.22.2-alpine AS build

WORKDIR /app

# Ensure npm selects Alpine (musl) optional native bindings from the lockfile.
ENV npm_config_platform=linux \
    npm_config_arch=x64 \
    npm_config_libc=musl

COPY package.json package-lock.json ./
RUN npm ci \
  && test -d node_modules/@rolldown/binding-linux-x64-musl \
  && test -d node_modules/@rollup/rollup-linux-x64-musl \
  && test -d node_modules/lightningcss-linux-x64-musl \
  && test -d node_modules/@tailwindcss/oxide-linux-x64-musl

COPY . .

# Same-origin API via Nginx proxy in Compose; override only if needed
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Unprivileged Nginx listens on 8080 (non-root)
FROM nginxinc/nginx-unprivileged:1.27.2-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
