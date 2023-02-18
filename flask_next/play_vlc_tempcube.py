# pre-reqs
# sudo apt update
# sudo apt install vlc -y


# importing vlc module
import vlc
import time

# creating vlc media player object
player = vlc.MediaPlayer(
    "/home/pi/workshop/LushRooms/faux_usb/tracks/Misophonia/ff-16b-2c-folder2.mp4")

# start playing audio
res = player.play()

print(f"res from player (zero is good) :: {res}")

time.sleep(0.5)

duration = player.get_length()

print(f"Duration of track in seconds :: {duration/1000}")

time.sleep(duration/1000)
