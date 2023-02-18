from os import uname, system
from time import sleep
import vlc
from vlc import State


# Useful vlc binding docs
# http://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

class VlcPlayer():
    def __init__(self):
        self.ready = False
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.paired = False
        self.masterIp = ""
        self.sourcePath = ""

    def primeForStart(self, pathToTrack):
        self.start(pathToTrack)

    def start(self, pathToTrack, syncTimestamp=None, master=False):
        print(f"Setting media to {pathToTrack}")
        self.player = vlc.MediaPlayer(pathToTrack)
        self.sourcePath = pathToTrack

        self.player.play()
        self.player.pause()
        sleep(1.5)
        self.player.audio_set_volume(80)
        print(f"After init, source :: {str(self.player.get_media())}")
        # self.player.play()
        print("************** Playing on vlc...",
              self.player.get_length() / 1000)
        return self.player.get_length() / 1000

    def status(self, status):
        if self.player != None:
            print('status requested from VLC player!')
            try:

                frontend_friendly_status = ""

                if self.player.get_state() == State.Playing:
                    frontend_friendly_status = "Playing"

                if self.player.get_state() == State.Paused:
                    frontend_friendly_status = "Paused"

                # if self.player.get_state() == State.Stopped:
                #     frontend_friendly_status = "Stopped"

                status["source"] = self.sourcePath
                status["playerState"] = frontend_friendly_status
                status["canControl"] = True
                status["position"] = self.player.get_time() / 1000
                status["trackDuration"] = self.player.get_length() / 1000
                status["error"] = ""
                status["paired"] = self.paired
                status["master_ip"] = self.masterIp
            except Exception as e:
                status["playerState"] = ""
                status["canControl"] = False
                status["error"] = "Something went wrong with player status request: " + \
                    str(e)

        else:
            status["playerState"] = ""
            status["canControl"] = False
            status["error"] = "Player is not initialized!"

        return status

    def playPause(self, syncTime=None):
        print("Playpausing...", self.player.get_length() / 1000)
        # self.start()
        # calling self.pause here has the effect of 'playing' the track (player.pause is a toggle...)

        if self.player.get_state() == State.NothingSpecial:
            print("State.NothingSpecial - attempting to play")
            self.player.play()
        elif self.player.get_state() == State.Stopped:
            print("State.Stopped - attempting to play")
            self.player.play()
        elif self.player.get_state() == State.Paused:
            print("State.Paused - attempting to play")
            self.player.play()
        elif self.player.get_state() == State.Playing:
            print("State.Playing - attempting to play")
            self.player.pause()

        print(f"After playPause, source :: {str(self.player.get_media())}")

        return self.player.get_length() / 1000

    def setPaired(self, val, masterIp):
        self.paired = val
        self.masterIp = masterIp
        print('paired set to: ', val)
        print('master_ip set to: ', masterIp)

    def getPosition(self):
        print("0:00")

    def pause(self):
        self.player.pause()

    def stop(self):
        print("Stopping...")

    def crossfade(self, nextTrack):
        print("Crossfading...")

    def next(self):
        print("Skipping forward...")

    def previous(self):
        print("Skipping back...")

    def mute(self):
        print(self.player.audio_get_volume())
        self.player.audio_set_volume(0)

    def volumeUp(self):
        self.player.audio_set_volume(self.player.audio_get_volume() + 10)

    def volumeDown(self, interval):
        print("vlc downer: ", self.player.audio_get_volume())
        if (self.player.audio_get_volume() <= 10 or interval == 0):
            return False
        else:
            self.player.audio_set_volume(
                self.player.audio_get_volume() - 100/interval)
            return True

    def exit(self, syncTimestamp=None):
        if self.player:
            self.player.stop()
        else:
            return 1

    def __del__(self):
        print("VLC died")
