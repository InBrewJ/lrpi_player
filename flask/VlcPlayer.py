from os import uname, system
from time import sleep
import vlc
from vlc import State
from time import ctime
import pause  # pylint: disable=import-error


# Useful vlc binding docs
# http://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

class VlcPlayer():
    def __init__(self):
        self.ready = False
        self.vlc_instance = vlc.Instance()
        self.player = None
        self.paired = False
        self.masterIp = ""
        self.sourcePath = ""

    def triggerStart(self, pathToTrack, withPause=False):
        # lrpi_player#105
        # Audio output can be routed through hdmi or the jack,
        # if settings.json is corrupted, default to the hdmi

        # todo - set volume via settings.json!
        # settings_json = settings.get_settings()
        # output_route = settings_json.get("audio_output")

        if not withPause:
            self.startWithPause(pathToTrack)
            self.player.play()
        elif withPause:
            self.startWithPause(pathToTrack)

    def primeForStart(self, pathToTrack):
        print("priming vlc for start - loading track in PAUSED state")
        self.triggerStart(pathToTrack, withPause=True)

    def startWithPause(self, pathToTrack):

        print(f"Setting media to {pathToTrack}")
        self.player = vlc.MediaPlayer(pathToTrack)
        self.sourcePath = pathToTrack

        # play the track at zero volume to get the info
        self.player.audio_set_volume(0)
        self.player.play()

        sleep(1.5)

        # pause, go back to the beginning,
        # set the volume back to something audible
        self.player.pause()
        self.player.set_position(0.0)
        self.player.audio_set_volume(80)

        print(f"After init, source :: {str(self.player.get_media())}")

    def start(self, pathToTrack, syncTimestamp=None, master=False):
        try:
            if not master:
                if self.player:
                    self.player.release()
                self.player = None

            if syncTimestamp:
                print(f"Pausing start until {syncTimestamp}")
                pause.until(syncTimestamp)

            if self.player is None or syncTimestamp is None:
                self.triggerStart(pathToTrack)

            # if volume is not None:
            #     self.audio_volume = volume
            #     print("Volume set to %s" % self.audio_volume)

            # self.player.set_volume(float(self.audio_volume)/100.0)

            print('synctime in vlcplayer: ', ctime(syncTimestamp))
            if master:
                self.player.play()
            print("************** Playing on vlc...",
                  self.player.get_length() / 1000)
            return self.player.get_length() / 1000
        except Exception as e:
            print("ERROR: Could not start player... but audio may still be playing!")
            print("Why: ", e)
            print("returning position 0...")
            return str(0)

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

        player_state = self.player.get_state()

        print("Playpausing :: state -> ", str(player_state))

        if player_state == State.NothingSpecial:
            print("State.NothingSpecial - attempting to play")
            self.player.play()
        elif player_state == State.Stopped:
            print("State.Stopped - attempting to play")
            self.player.play()
        elif player_state == State.Paused:
            print("State.Paused - attempting to play")
            self.player.play()
        elif player_state == State.Playing:
            print("State.Playing - attempting to pause")
            self.player.pause()

        print(f"After playPause, source :: {str(self.player.get_media())}")

        return self.player.get_length() / 1000

    def setPaired(self, val, masterIp):
        self.paired = val
        self.masterIp = masterIp
        print('paired set to: ', val)
        print('master_ip set to: ', masterIp)

    def getPosition(self):
        return self.player.get_time() / 1000

    def seek(self, position0_to_100):
        to_0_to_1 = float(position0_to_100) / 100
        print(f"Telling vlc player to seek to {to_0_to_1}")
        self.player.set_position(to_0_to_1)
        return self.getPosition()

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
