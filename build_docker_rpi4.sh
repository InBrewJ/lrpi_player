# lushroom-player Dockerfile, rpi4 edition (64 bit, mpv based)

BUILD_DIR="./docker-builds"

echo "***** Building Lushrooms Pi Rpi4..."

mkdir $BUILD_DIR || true && \
sudo docker build -t lushroom-player:64-bit-mpv -f ./Dockerfile.rpi4.64bit . && \
echo "***** Saving Lushrooms Pi Rpi4 img to tarball..." && \
docker save -o $BUILD_DIR/lrpi4-img-64.tar lushroom-player:64-bit-mpv && \
echo "***** Lushrooms Pi Rpi4 images built and saved..." && \
echo "***** Tarred up image: " && \
ls -lah $BUILD_DIR
