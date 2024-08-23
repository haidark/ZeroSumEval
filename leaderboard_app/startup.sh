#!/bin/bash

# Start Nginx
nginx -g "daemon off;" &

# Start FastAPI
cd $HOME/app/backend
fastapi run &

cd $HOME/app/react_app
npm run start &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?