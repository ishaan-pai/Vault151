# Build the static site, then serve it from nginx. Chosen over shipping the Vite
# dev server so the container matches how production will actually run.
FROM node:22-alpine AS build

WORKDIR /app

# package-lock.json must exist: run `npm install` once on the host first.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
