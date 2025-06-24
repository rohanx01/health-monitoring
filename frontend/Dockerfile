# --- Stage 1: The Build Stage ---
# Use an official Node.js image to build our React app
FROM node:18-alpine as builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first
# This leverages Docker's layer caching
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the React app for production
# This creates a static 'build' folder
RUN npm run build

# --- Stage 2: The Production Stage ---
# Use a tiny, efficient web server to serve our static files
FROM nginx:1.23-alpine

# Copy the build output from the 'builder' stage
COPY --from=builder /app/build /usr/share/nginx/html

# Nginx will automatically serve the index.html file from this directory
# Expose port 80 for the Nginx server
EXPOSE 80