# vaugely helpful gist on alsa config
# https://gist.github.com/rnagarajanmca/63badce0fe0e2ad126041c7c139970ea


# audio only thread, mentions 5.1
# https://forums.raspberrypi.com/viewtopic.php?t=316340
# the original 3A thread
# https://forums.raspberrypi.com/viewtopic.php?t=307369
# some pointers for dt-overlay
# https://www.phoronix.com/forums/forum/software/distributions/1306237-raspberry-pi-s-raspbian-os-finally-spins-64-bit-version


# top level how to
# add this to /boot/config.txt in [pi4] section
# settings for 5.1 output via mpv player

# enable sound from hdmi
# hdmi_drive=2
# enable audio
# dtparam=audio=on
# hdmi_stream_channels=1
# hdmi_channel_map=335201480
# hdmi ports will appear in alsamixer?
# hdmi_force_hotplug=1
# enable hardware decoding for h.264 / h.265
# dtoverlay=vc4-kms-v3d,cma-512
# dtoverlay=rpivid-v4l2


import mpv
from time import sleep

# to get this working see this:
# https://github.com/jaseg/python-mpv/issues/154
# https://github.com/Wikinaut/pinetradio -> for a working example
# Because of out of date Debian repos, this installs py mpv v0.5.2
# https://github.com/jaseg/python-mpv/tree/v0.5.2
#
#

# Some help for Alsa surround sound
# https://github.com/mpv-player/mpv/wiki/ALSA-Surround-Sound-and-Upmixing

# audio output seems to be controlled entirely via alsa - hm
# or: https://mpv.io/manual/master/#audio-output-drivers-alsa
# can it be changed via an IPC command?


# files load from the usb stick just fine, mount usb stick with
# sudo mount /dev/sda1 /mnt/usb1/
# (or something similar)
path_to_track = '/mnt/usb1/lushrooms2023/02_Tales_of_bath_Poem.mp4'

global player

player = mpv.MPV(ytdl=False, input_default_bindings=True,
                 input_vo_keyboard=False)


def start():
    global player

    if player is None:
        print('PLAYER WAS NONE on a call to start()')
        player = mpv.MPV(ytdl=False, input_default_bindings=True,
                         input_vo_keyboard=False)

    # Property access, these can be changed at runtime
    @player.property_observer('time-pos')
    def time_observer(_name, value):
        # Here, _value is either None if nothing is playing or a float containing
        # fractional seconds since the beginning of the file.
        if value is not None:
            # print(f'Now playing at {value:.2f}s')
            pass

    @player.property_observer('pause')
    def time_observer(_name, value):
        if value is not None:
            print(f'property.pause = {value}')

    @player.property_observer('volume')
    def volume_observer(_name, value):
        if value is not None:
            print(f'property.volume = {value}')

    @player.property_observer('core-idle')
    def core_idle_observer(_name, value):
        if value is not None:
            print(
                f'******************* CORE IDLE CHANGED = {value} *******************')

    player['volume'] = 87

    player.play(path_to_track)

    player.wait_until_playing()

    sleep(1)

    seek_to = 10

    print(f'seek to {seek_to}%')

    player.seek(seek_to, reference='absolute-percent')


def stop():
    global player
    print('Stopping...')
    player.command('stop')


def kill():
    global player
    print('Killing via del player...')
    del player
    player = None

# how to start with a defined volume?


start()

sleep(2)

print("switching to alsa/surround51 device...")

# this _does_ work to change the audio device
# I'm reasoning this because trying to change the audio device to e.g.
# alsa/sysdefault:CARD=vc4hdmi15 results in mpv throwing an error
# start might not work unless something is plugged in to the port?
# testing required!
# player["audio-device"] = 'alsa/sysdefault:CARD=vc4hdmi0'

player["audio-device"] = 'alsa/surround51'

stop()

sleep(2)

kill()

print("switching back to headphone jack...")

start()

sleep(1)

print("switching to a slightly different headphone device")

player["audio-device"] = 'alsa/plughw:CARD=Headphones,DEV=0'

start()

sleep(6)


# also see this project that uses the IPC API
# https://github.com/iwalton3/python-mpv-jsonipc

# 5.1 surround adventures
# https://forums.raspberrypi.com/viewtopic.php?t=250879
# https://forums.raspberrypi.com/viewtopic.php?t=307369

# this outputs 6 channels out of the headphone jack
# speaker-test -c6 -D hw:0,0

# https://github.com/mpv-player/mpv/issues/3955
# mpv cli, get available devices with
# mpv --audio-device=help
# returns
# List of detected audio devices:
#   'auto' (Autoselect device)
#   'alsa' (Default (alsa))
#   'alsa/output' (output)
#   'alsa/plughw:CARD=Headphones,DEV=0' (bcm2835 Headphones, bcm2835 Headphones/Hardware device with all software conversions)
#   'alsa/sysdefault:CARD=Headphones' (bcm2835 Headphones, bcm2835 Headphones/Default Audio Device)
#   'alsa/dmix:CARD=Headphones,DEV=0' (bcm2835 Headphones, bcm2835 Headphones/Direct sample mixing device)
#   'alsa/plughw:CARD=vc4hdmi0,DEV=0' (vc4-hdmi-0, MAI PCM i2s-hifi-0/Hardware device with all software conversions)
#   'alsa/sysdefault:CARD=vc4hdmi0' (vc4-hdmi-0, MAI PCM i2s-hifi-0/Default Audio Device)
#   'alsa/hdmi:CARD=vc4hdmi0,DEV=0' (vc4-hdmi-0, MAI PCM i2s-hifi-0/HDMI Audio Output)
#   'alsa/dmix:CARD=vc4hdmi0,DEV=0' (vc4-hdmi-0, MAI PCM i2s-hifi-0/Direct sample mixing device)
#   'alsa/plughw:CARD=vc4hdmi1,DEV=0' (vc4-hdmi-1, MAI PCM i2s-hifi-0/Hardware device with all software conversions)
#   'alsa/sysdefault:CARD=vc4hdmi1' (vc4-hdmi-1, MAI PCM i2s-hifi-0/Default Audio Device)
#   'alsa/hdmi:CARD=vc4hdmi1,DEV=0' (vc4-hdmi-1, MAI PCM i2s-hifi-0/HDMI Audio Output)
#   'alsa/dmix:CARD=vc4hdmi1,DEV=0' (vc4-hdmi-1, MAI PCM i2s-hifi-0/Direct sample mixing device)
#   'jack' (Default (jack))
#   'sdl' (Default (sdl))
#   'sndio' (Default (sndio))
