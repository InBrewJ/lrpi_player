# install mpv on linux systems like this
# sudo apt install mpv libmpv-dev python3-mpv
# not entirely sure how to get it running on MacOS just yet...

import mpv
from time import sleep

# to get this working see this:
# https://github.com/jaseg/python-mpv/issues/154
# https://github.com/Wikinaut/pinetradio -> for a working example
# Because of out of date Debian repos, this installs py mpv v0.5.2
# https://github.com/jaseg/python-mpv/tree/v0.5.2
#

# Some help for Alsa surround sound
# https://github.com/mpv-player/mpv/wiki/ALSA-Surround-Sound-and-Upmixing

# also this - set audio-channels=auto
# https://mpv.io/manual/master/#audio-output-drivers-alsa

path_to_track = '/home/inbrewj/workshop/LushRooms/faux_usb/tracks/17_Tales_of_bath/02_Tales_of_bath_Poem.mp4'


player = mpv.MPV(ytdl=False, input_default_bindings=True,
                 input_vo_keyboard=False, pause=True, audio_channels='auto', log_handler=print)
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


player['volume'] = int(2 * 42)

print("starting, but paused")

player.play(path_to_track)
player.wait_until_paused()

# If we can figure alsa configs out, we can decouple mpv audio devices from board specific devices; they will depend on the device definitions we set up in alsa
#
# hdmi = alsa/hdmiSurround51
# jack = alsa/headphoneJackStereo
# the above will work with the contents of 'mpv_test/asoundrc_example_51' saved in /etc/asound.conf
# Get audio devices on your machine with
# mpv --audio-device=help

###########################
# CHANGE AUDIO DEVICE HERE
###########################
# 'auto' and 'alsa' should work if alsa is working correctly
player["audio-device"] = 'alsa'

sleep(1)


print("unpausing")
player["pause"] = False

player.wait_until_playing()


# blocking process, script will exit when the track finishes
player.wait_for_playback()
