docker run -it --rm -p 80:80 -v /opt/vc:/opt/vc -v /media/usb:/media/usb --device /dev/vchiq:/dev/vchiq --device /dev/fb0:/dev/fb0 --entrypoint "/bin/bash" lushdigital/lushroom-player:staging  
