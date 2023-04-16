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
lushroom-player-rpi4:32bit


# --restart=always \

# or, for 64bit, from docker hub

sudo docker run -it --rm --network host -p 80:80 \
--env PORT=80 \
-v $HOME/.pulse:/home/vlc/.pulse:rw \
-v /dev/shm:/dev/shm \
-v /dev/snd:/dev/snd \
-v /var/lib/dbus:/var/lib/dbus \
-v /media/usb:/media/usb \
--privileged \
--device /dev/vchiq:/dev/vchiq \
inbrewj/lushroom-player-rpi4:64bit


# or, for 64bit, from lushdigital docker hub
# not convinced we need to dbus line

sudo docker run -it --rm --network host -p 80:80 \
--env PORT=80 \
-v $HOME/.pulse:/home/vlc/.pulse:rw \
-v /dev/shm:/dev/shm \
-v /dev/snd:/dev/snd \
-v /var/lib/dbus:/var/lib/dbus \
-v /media/usb:/media/usb \
--privileged \
--device /dev/vchiq:/dev/vchiq \
lushdigital/lushroom-player:64bit