FROM nikolaik/python-nodejs:python3.10-nodejs20

# Set home to the user's home directory
ENV HOME=/home/pn \
	PATH=/home/pn/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

RUN chown -R pn:pn $HOME

# Install system dependencies
RUN apt-get update && apt-get install -y supervisor nginx

RUN apt-get update && apt-get install git-lfs -y
RUN git lfs install

# Copy and install Python dependencies
COPY --chown=pn backend/requirements.txt $HOME/app/
RUN pip install -r requirements.txt

# Copy and install Node.js dependencies
COPY --chown=pn react_app/package.json react_app/package-lock.json* $HOME/app/react_app/
RUN cd react_app && npm install

# Copy the rest of the application
COPY --chown=pn backend $HOME/app/backend
COPY --chown=pn react_app $HOME/app/react_app

# Build the React app
RUN cd react_app && REACT_APP_API_URL=/api npm run build

# Set up Nginx
COPY --chown=pn nginx.conf /etc/nginx/nginx.conf

# # Change ownership of critical directories
RUN chown -R pn:pn /var/lib/nginx \
    && chown -R pn:pn /run 

COPY --chown=pn startup.sh $HOME/app/startup.sh

# Switch to non-root user
USER pn

# Expose the Nginx port
EXPOSE 7860

# Start supervisord
CMD ["/bin/bash", "./startup.sh"]
