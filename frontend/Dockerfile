# MediSecure frontend — multi-stage build for Nginx
FROM node:22.11.0-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27.2-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

RUN addgroup -g 10001 -S appuser \
  && adduser -S -D -H -u 10001 -G appuser appuser \
  && chown -R appuser:appuser /usr/share/nginx/html /var/cache/nginx /var/log/nginx \
  && touch /var/run/nginx.pid && chown appuser:appuser /var/run/nginx.pid

USER appuser
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
