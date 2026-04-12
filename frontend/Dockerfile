# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Template is processed manually so only ${PORT} and ${BACKEND_URL} are substituted,
# leaving nginx variables like $host and $uri untouched.
COPY nginx.conf /etc/nginx/default.conf.template

ENV PORT=8080
ENV BACKEND_URL=http://localhost:8000
EXPOSE 8080
CMD ["/bin/sh", "-c", "envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
