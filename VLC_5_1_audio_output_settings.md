# Pushing 5.1 surround sound audio from an HDMI port on a Pi-like SBC

Inspired by:

- https://forums.raspberrypi.com/viewtopic.php?t=307369
- https://steamcommunity.com/app/353380/discussions/6/1743353164095764346/?l=english&ctp=3
- https://steamcommunity.com/app/353380/discussions/6/1642042464753800526/

## /boot/config.txt

(Only applicable for a Pi)

The config.txt must include

```
hdmi_drive=2
dtparam=audio=on
hdmi_stream_channels=1
hdmi_channel_map=335201480
hdmi_force_hotplug=1
```

Also try `200983752` or `335201928` in the 'hdmi_channel_map' field

## /etc/asound.conf

```
pcm.!surround51 {
type route
slave.pcm "hw:0,0"
slave.channels 8
ttable {
0.0= 1
1.1= 1
2.4= 1
3.5= 1
4.2= 1
5.3= 1
6.6= 0
7.7= 0
}
}
```

## Python script to find available audio devices

See `lrpi_player/vlc_test/get_available_devices.py`

## Simple python-vlc script that uses the surround51 configured above

See `lrpi_player/vlc_test/use_5_1_device_vlc.py`
