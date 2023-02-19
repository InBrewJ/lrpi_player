from os import uname, system
from time import sleep
import vlc
from vlc import State
from time import ctime
import pause  # pylint: disable=import-error
import settings


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
        # if settings.json is corrupted, default to the jack

        # todo - set volume via settings.json!
        # settings_json = settings.get_settings()
        # output_route = settings_json.get("audio_output")

        settings_json = settings.get_settings()
        output_route = settings_json.get("audio_output")
        normalised_audio_device_output = 'alsa_output.platform-bcm2835_audio.analog-stereo'

        if output_route == 'hdmi':
            normalised_audio_device_output = 'to_find'
            # see /lrpi_player/VLC_5_1_audio_output_settings.md
            SUSPECTED_5_1_DMI_DEVICE_ID = "alsa_output.platform-vc4-hdmi-0_audio.surround51"
        elif output_route == 'jack':
            normalised_audio_device_output = 'alsa_output.platform-bcm2835_audio.analog-stereo'

        if not withPause:
            self.startWithPause(pathToTrack)
            # Not sure yet where the best place to call audio_output_device_set is
            # self.player.audio_output_device_set(
            #     None, normalised_audio_device_output)

            # calling stop here to pick up the audio device change
            # self.player.stop()
            self.player.play()
        elif withPause:
            self.startWithPause(pathToTrack)
            # self.player.audio_output_device_set(
            #     None, normalised_audio_device_output)

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
        sleep(0.25)
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

                # I'm not entirely sure what the tablet ui does
                # if the status retured = "Stopped"...
                #
                if self.player.get_state() == State.Stopped:
                    frontend_friendly_status = "Stopped"

                status["source"] = self.sourcePath
                status["playerState"] = frontend_friendly_status
                status["canControl"] = True
                status["position"] = self.player.get_time() / 1000
                status["trackDuration"] = self.player.get_length() / 1000
                status["error"] = ""
                status["paired"] = self.paired
                status["master_ip"] = self.masterIp
            except Exception as e:
                status["playerState"] = "UNKNOWN"
                status["canControl"] = False
                status["error"] = "Something went wrong with player status request: " + \
                    str(e)

        else:
            status["playerState"] = ""
            status["canControl"] = False
            status["error"] = "Player is not initialized!"

        return status

    def playPauseToggler(self):
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

    def playPause(self, syncTimestamp=None):
        print("Playpausing...", self.player.get_length() / 1000)

        if syncTimestamp:
            pause.until(syncTimestamp)

        self.playPauseToggler()

        print(f"After playPause, source :: {str(self.player.get_media())}")

        return self.player.get_length() / 1000

    def setPaired(self, val, masterIp):
        self.paired = val
        self.masterIp = masterIp
        print('paired set to: ', val)
        print('master_ip set to: ', masterIp)

    def getPosition(self):
        return self.player.get_time() / 1000

    def seek(self, position0_to_100, syncTimestamp=None):

        if syncTimestamp:
            pause.until(syncTimestamp)

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
        start_volume = 80
        step = int(int(start_volume / int(interval)) / 4)

        current_volume = self.player.audio_get_volume()

        print("vlc downer: ", str(current_volume))
        # Vlc volume is between 0 and 100
        # below 10 is barely audible, ready for crossfading!
        if (current_volume <= 7 or interval == 0):
            # False =  we can't lower the volume anymore
            return False
        else:
            print(
                f"Ideal next step based on i: {interval} -> ", step)
            next_volume_step_down = current_volume - step
            if (next_volume_step_down < 0):
                next_volume_step_down = 0
            self.player.audio_set_volume(next_volume_step_down)
            # True = the volume is not yet at a minimum
            return True

    def exit(self, syncTimestamp=None):
        if self.player:
            print("Stopping VLC")
            # self.player.stop()
            self.__del__()
        else:
            return 1

    def __del__(self):
        if self.player:
            self.player.release()
            self.player = None
        print("VLC died")
