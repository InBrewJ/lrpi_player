# inspired by
# https://stackoverflow.com/questions/73884593/how-to-change-vlc-python-output-device/73886462


import vlc

# change this to path on your local machine
MP4_AUDIO_PATH = "/home/pi/workshop/LushRooms/faux_usb/tracks/Graphic/Graphic.mp4"

# Create VLC instance, media player and media
instance = vlc.Instance()
player = instance.media_player_new()
media = instance.media_new(MP4_AUDIO_PATH)
player.set_media(media)


def get_available_devices(playerI):
    mods = playerI.audio_output_device_enum()
    if mods:
        mod = mods
        while mod:
            mod = mod.contents
            print("*" * 30)
            print(f"device {mod.device}")
            print("*" * 30)
            print(f"description: {mod.description}")
            print(f"device id: {mod.device}")
            print("*" * 30)
            mod = mod.next


get_available_devices(player)
