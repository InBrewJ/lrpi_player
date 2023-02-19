# LushRoom Pi player

Cloud connected sound and light player for Lush treatment rooms

Flask/omxplayer/vlcplayer/DMX/HUE/Tinkerforge/SRT

## Local, VLC centric dev

Because VLC should work everywhere, right?

### venv

- Create with

```
python3 -m venv ./.venv_lrpi_player
```

- and then, the classic

```
source ./.venv_lrpi_player/bin/activate
```

### Mount lrpi_player code on a remote linux machine to a LushRooms dev environment (a Pi / Banana / Potato / whatever)

- Install `openssh-server` on the remote machine

```
sudo apt install openssh-server
```

- Install sshfs on the dev environment

```
sudo apt update
sudo apt install sshfs
```

- Mount the remote `lrpi_player` directory

```
sudo sshfs -o allow_other,default_permissions inbrewj@pop-os:/home/inbrewj/workshop/LushRooms/lrpi_player ~/workshop/LushRooms/lrpi_player
```

- Start with faux_usb

```
sudo LRPI_SETTINGS_PATH=~/workshop/LushRooms/faux_usb/settings.json python3 -u flask/Server.py
```

## Helpers

Sample sshfs command:

```
sudo sshfs -o allow_other,defer_permissions,IdentityFile=./lrpi_id_rsa lush@xxx.xxx.xxx.xxx:/home/lush ./mnt
```

Run dev code inside a running Dockerised player (only works on a 'Pi!):

In Pod mode:

```
sudo docker run --env MENU_DMX_VAL="255,172,36" --env NUM_DMX_CHANNELS=192 -it --rm -p 80:80 \
-v /home/lush/lrpi_player/flask:/opt/code/flask \
-v /opt/vc:/opt/vc \
-v /media/usb:/media/usb \
--env BRICKD_HOST=localhost \
--network host \
--device /dev/vchiq:/dev/vchiq \
--device /dev/fb0:/dev/fb0 \
lushdigital/lushroom-player:staging
```

In Spa mode:

```
sudo docker run -it --rm -p 80:80 \
-v /home/lush/lrpi_player/flask:/opt/code/flask \
-v /opt/vc:/opt/vc \
-v /media/usb:/media/usb \
--env BRICKD_HOST=localhost \
--network host \
--device /dev/vchiq:/dev/vchiq \
--device /dev/fb0:/dev/fb0 \
lushdigital/lushroom-player:staging
```

Run a bash terminal for in depth debugging:

```
docker run -it --rm -p 80:80 -v /opt/vc:/opt/vc -v /media/usb:/media/usb --device /dev/vchiq:/dev/vchiq --device /dev/fb0:/dev/fb0 --entrypoint "/bin/bash" lushdigital/lushroom-player:staging

```
