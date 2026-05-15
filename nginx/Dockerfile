FROM node:20-alpine AS frontend-build

WORKDIR /web
COPY SuKyAI_Web/package*.json ./
RUN npm ci

COPY SuKyAI_Web/index.html ./index.html
COPY SuKyAI_Web/vite.config.js ./vite.config.js
COPY SuKyAI_Web/public ./public
COPY SuKyAI_Web/src ./src

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY SuKyAI_API/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /web/dist /usr/share/nginx/html
