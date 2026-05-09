FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_USE_RELATIVE_API=true
ENV VITE_USE_RELATIVE_API=$VITE_USE_RELATIVE_API

RUN npm run build

FROM nginx:alpine

COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
