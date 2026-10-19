FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Vazio = chamadas em /api na mesma origem (proxy do nginx abaixo)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Etapa 2: arquivos estáticos servidos pelo nginx
FROM nginx:1.27-alpine
# Destino do proxy /api/ (sobrescreva com -e API_UPSTREAM=... ou no compose)
ENV API_UPSTREAM=http://backend:5000 \
    NGINX_RESOLVER=127.0.0.11 \
    NGINX_ENVSUBST_FILTER="^(API_UPSTREAM|NGINX_RESOLVER)$"
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
