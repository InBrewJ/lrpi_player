# 8686 for weird lumicube stuff - soon to be a problem of the past...

# devices / volumes inspired by:
# https://github.com/scottsideleau/docker-vlc

PORT=8686

sudo docker run -it --rm --network host -p $PORT:$PORT \
--env PORT=$PORT \
-v $HOME/.pulse:/home/vlc/.pulse:rw \
-v /dev/shm:/dev/shm \
-v /dev/snd:/dev/snd \
-v /var/lib/dbus:/var/lib/dbus \
-v /media/usb:/media/usb \
--privileged \
--device /dev/vchiq:/dev/vchiq \
lushroom-player-rpi4.32bit:latest


# --restart=always \