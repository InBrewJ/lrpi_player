import vlc
from time import sleep

# It MIGHT be the case that VLC picks up the audio device based on which one is plugged in
# e.g. nothing plugged into the jack, something plugged into hdmi0, vlc will send audio out of hdmi0 and so on

# change this to path on your local machine
MP4_AUDIO_PATH = "/home/pi/workshop/LushRooms/faux_usb/tracks/Graphic/Graphic.mp4"

RPI_4_HEADPHONE_OUTPUT = "alsa_output.platform-bcm2835_audio.analog-stereo"

DEVICE_ID_5_1_HDMI = "find my device id with lrpi_player/vlc_test/get_available_devices.py"

# hdmi port 0 is closest to the power connector
# hdmi port 1 is closest to the audio jack
SUSPECTED_5_1_DMI_DEVICE_ID = "alsa_output.platform-vc4-hdmi-0_audio.surround51"

# Create VLC instance, media player and media
instance = vlc.Instance()
player = instance.media_player_new()
media = instance.media_new(MP4_AUDIO_PATH)
player.set_media(media)


# player.audio_output_device_set(None, RPI_4_HEADPHONE_OUTPUT)

player.stop()

sleep(1)

player.play()
print("Setting audio device")
player.audio_output_device_set(None, RPI_4_HEADPHONE_OUTPUT)

sleep(1)

player.stop()

sleep(1)

player.play()

input("Press enter to exit")
