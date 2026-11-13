# MediSecure static portal — unprivileged Nginx on port 8080
FROM nginxinc/nginx-unprivileged:1.27.2-alpine

# Install static content and config as the nginx runtime user (UID 101)
USER root
COPY --chown=101:101 --chmod=644 index.html /usr/share/nginx/html/index.html
COPY --chown=101:101 --chmod=644 nginx.conf /etc/nginx/conf.d/default.conf
RUN chmod 755 /etc/nginx /etc/nginx/conf.d \
  && chmod 644 /etc/nginx/conf.d/default.conf \
  && chown -R 101:101 /usr/share/nginx/html

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
