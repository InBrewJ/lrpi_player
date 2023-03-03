#! /bin/bash

BUILD_DIR="./docker-builds"
PROJECT_DIR="/home/pi/workshop/LushRooms/docker_builds"
HOST="tempcube.local"
HOST_USER="pi"

echo "***** Copying images to $HOST"
echo "***** (this may take a while depending on your network speed)"

scp $BUILD_DIR/lrpi4-img-32.tar $HOST_USER@$HOST:$PROJECT_DIR


echo "***** Deployment to host: $HOST complete."


printf "\n\nDone."

# Then, on host:

# docker load -i /home/pi/workshop/LushRooms/docker_builds/lrpi4-img-32.tar

# to run, see ./run_rpi4_32.sh
