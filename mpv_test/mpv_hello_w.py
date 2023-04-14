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

player = mpv.MPV(ytdl=False, input_default_bindings=True,
                 input_vo_keyboard=False)

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
        print(f'property.ao-volume = {value}')

# how to start with a defined volume?


player['volume'] = 50

player.play(
    '/home/jib/workshop/LushRooms/faux_usb/tracks/17_Tales_of_bath/02_Tales_of_bath_Poem.mp4')

player.wait_until_playing()

# and some commands
sleep(3)

print('pausing...')

player["pause"] = True

sleep(3)

print("Playing again...")

player["pause"] = False

sleep(2)

print("Jumping volume up to 79")

player['volume'] = 79

sleep(3)

print("Exiting...")

del player


# also see this project that uses the IPC API
# https://github.com/iwalton3/python-mpv-jsonipc
