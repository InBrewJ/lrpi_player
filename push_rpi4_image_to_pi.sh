#! /bin/bash

BUILD_DIR="./docker-builds"
PROJECT_DIR="/home/jib/workshop/LushRooms/docker_builds"
MASTER_HOST="redcube.local"
SLAVE_HOST="greencube.local"
HOST_USER="jib"

echo "***** Copying images to $HOST"
echo "***** (this may take a while depending on your network speed)"

scp $BUILD_DIR/lrpi4-img-64.tar $HOST_USER@$MASTER_HOST:$PROJECT_DIR
scp $BUILD_DIR/lrpi4-img-64.tar $HOST_USER@$SLAVE_HOST:$PROJECT_DIR


echo "***** Deployment to host: $HOST complete."


printf "\n\nDone."

# Then, on host:

# docker load -i /home/jib/workshop/LushRooms/docker_builds/lrpi4-img-64.tar

# to run, see ./run_rpi4_32.sh
