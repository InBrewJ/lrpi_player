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

path_to_track = '/mnt/usb1/lushrooms2023/tracks/17_Tales_of_bath/02_Tales_of_bath_Poem.mp4'
# path_to_track = '/home/inbrewj/workshop/LushRooms/faux_usb/tracks/17_Tales_of_bath/02_Tales_of_bath_Poem.mp4'

player = mpv.MPV(ytdl=False, input_default_bindings=True,
                 input_vo_keyboard=False, pause=True, log_handler=print)
player.set_loglevel('v')
player.wait_for_property('idle-active')

# Property access, these can be changed at runtime
@player.property_observer('time-pos')
def time_observer(_name, value):
    # Here, _value is either None if nothing is playing or a float containing
    # fractional seconds since the beginning of the file.
    if value is not None:
        print(f'Now playing at {value:.2f}s')


@player.property_observer('pause')
def time_observer(_name, value):
    if value is not None:
        print(f'property.pause = {value}')


@player.property_observer('volume')
def volume_observer(_name, value):
    if value is not None:
        print(f'property.volume = {value}')

# how to start with a defined volume?


player['volume'] = 61

print("starting, but paused")

player.play(path_to_track)
player.wait_until_paused()
# player.wait_for_property('idle-active')

sleep(2)

seek_to = 10
print(f'seek to {seek_to}%')

player.seek(seek_to, reference='absolute-percent')


print("unpausing")
player["pause"] = False

player.wait_until_playing()
# If we can figure alsa configs out, we can decouple mpv audio devices from board specific devices; they will depend on the device definitions we set up in alsa
#
# hdmi = alsa/hdmiSurround51
# jack = alsa/headphoneJackStereo
# the above will work with the contents of 'mpv_test/asoundrc_example_51' saved in /etc/asound.conf
player["audio-device"] = 'alsa/headphoneJackStereo'


# and some commands
sleep(10)

print('pausing...')

player["pause"] = True

sleep(3)

print("Playing again...")

player["pause"] = False

sleep(2)

print("Jumping volume up to 79")

player['volume'] = 79

sleep(3)

print('stopping...')

player.command('stop')

sleep(2)

print('starting again...')

player.play(path_to_track)

player.wait_until_playing()


sleep(5)

seek_to = 10

print(f'seek to {seek_to}%')

player.seek(seek_to, reference='absolute-percent')

sleep(5)

print("Exiting... (deleting player object via python)")

del player


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
