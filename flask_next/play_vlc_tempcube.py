# pre-reqs
# sudo apt update
# sudo apt install vlc -y

# Attempts to force VLC to output sound from the HDMI ports
# inspired by https://forums.raspberrypi.com/viewtopic.php?t=307369

# Steps
# Find all possible audio output devices on a Pi 4
#### aplay -l
####


# importing vlc module
import vlc
import time


MP4_AUDIO_PATH = "/home/pi/workshop/LushRooms/faux_usb/tracks/Graphic/Graphic.mp4"

# creating vlc media player object
player = vlc.MediaPlayer(MP4_AUDIO_PATH)

# start playing audio
res = player.play()

print(f"res from player.play (zero is good) :: {res}")

time.sleep(0.5)

duration = player.get_length()

# Pi4
# hdmi audio 'cards' appear as devices with names:
# vc4-hdmi-0
# vc4-hdmi-1


time.sleep(0.5)

audio_output_devices = player.audio_output_device_enum()


def get_device(playerI):
    mods = playerI.audio_output_device_enum()
    print(f"mods : {mods}")
    if mods:
        mod = mods
        while mod:
            mod = mod.contents
            print("*" * 30)
            print("possible audio output device below...")
            print("*" * 30)
            print(mod.description)
            print(mod.device)
            print("*" * 30)
            # Find the HDMI output here...
            # It would seem that the hdmi devices don't appear unless something is plugged into them?
            if 'CABLE Input (VB-Audio Virtual Cable)' in str(mod.description):
                device = mod.device
                module = mod.description
                return device, module
            mod = mod.next


get_device(player)

print(f"Current audio device :: {player.audio_output_device_get()}")
# e.g. alsa_output.platform-bcm2835_audio.analog-stereo

# Attempts to set audio device
device_id = "alsa_output.platform-bcm2835_audio.analog-stereo"
player.audio_output_device_set(None, device_id)

output_set_res = player.audio_output_device_set(None, device_id)

print(f"res from audio_output_set (zero is good) :: {output_set_res}")

# must be stopped for output setting to work
player.stop()

time.sleep(0.5)

player.play()

print(f"Duration of track in seconds :: {duration/1000}")

time.sleep(duration/1000)
