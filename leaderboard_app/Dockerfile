FROM nikolaik/python-nodejs:python3.10-nodejs20

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y supervisor nginx

RUN apt-get update && apt-get install git-lfs -y
RUN git lfs install

# Copy and install Python dependencies
COPY backend/requirements.txt /app/
RUN pip install -r requirements.txt

# Copy and install Node.js dependencies
COPY react_app/package.json react_app/package-lock.json* /app/react_app/
RUN cd react_app && npm install

# Copy the rest of the application
COPY backend /app/backend
COPY react_app /app/react_app

# Build the React app
RUN cd react_app && REACT_APP_API_URL=/api npm run build

# Set up supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set up Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/run/supervisor && \
    chown -R pn:pn /var/log/supervisor /var/run/supervisor /etc/supervisor /var/run/nginx /var/log/nginx /etc/nginx

# Switch to non-root user
USER pn

# Expose the Nginx port
EXPOSE 7860

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]