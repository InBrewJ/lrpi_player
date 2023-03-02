# lushroom-player Dockerfile, rpi4 edition

BUILD_DIR="./docker-builds"

echo "***** Building Lushrooms Pi Rpi4..."

mkdir $BUILD_DIR || true && \
sudo docker build -t lushroom-player-rpi4 -f ./Dockerfile.rpi4 . && \
echo "***** Saving Lushrooms Pi Rpi4 img to tarball..." && \
docker save -o $BUILD_DIR/lrpi4-img.tar lushroom-player-rpi4 && \
echo "***** Lushrooms Pi Rpi4 images built and saved..." && \
echo "***** Tarred up image: " && \
ls -lah $BUILD_DIR
