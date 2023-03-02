#! /bin/bash

BUILD_DIR="./docker-builds"
PROJECT_DIR="/home/pi/workshop/LushRooms/docker_builds"
HOST="tempcube.local"
HOST_USER="pi"

echo "***** Copying images to $HOST"
echo "***** (this may take a while depending on your network speed)"

scp $BUILD_DIR/lrpi4-img.tar $HOST_USER@$HOST:$PROJECT_DIR


echo "***** Deployment to host: $HOST complete."


printf "\n\nDone."

# Then, on host:

# docker load -i /home/pi/workshop/LushRooms/docker_builds/lrpi4-img.tar

# again, 8686 is for weird lumicube reasons
# remember the PORT env var!
# can be set in the docker-compose / swarm / stack / whatever
# docker run --rm -d -p 8686:8686 --name lrpi-player-rpi4 lushroom-player-rpi4
