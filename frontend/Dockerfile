# Stage 1: Build the frontend application
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json /app/

# Install dependencies
RUN npm ci

# Copy application source code
COPY . /app

# Build application (generates dist folder)
RUN npm run build

# Stage 2: Serve the build directory using Nginx
FROM nginx:alpine

# Copy static assets from build stage to nginx folder
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 5173
EXPOSE 5173

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
