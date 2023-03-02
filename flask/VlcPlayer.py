from os import uname, system
from time import sleep
import vlc
from vlc import State
from time import ctime
import pause  # pylint: disable=import-error
import settings

# todo:
# create singleton for vlc.Instance
# there should only ever be one, no exceptions!


# Useful vlc binding docs
# http://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

class VlcPlayer():
    def __init__(self):
        self.ready = False
        self.instance = vlc.Instance()
        self.vlcPlayer = self.instance.media_player_new()
        self.paired = False
        self.masterIp = ""
        self.sourcePath = ""
        settings_json = settings.get_settings()
        self.initialVolumeFromSettings: int = int(
            settings_json["audio_volume"])

    def getAudioOutput(self, settings_json):
        # lrpi_player#105
        # Audio output can be routed through hdmi or the jack,
        # if settings.json is corrupted, default to the jack
        output_route = settings_json.get("audio_output")

        # output_route is jack or hdmi...

        # platform-bcm2835_audio.analog-stereo is the jack on RPi4
        normalised_audio_device_output = 'alsa_output.platform-bcm2835_audio.analog-stereo'
        return normalised_audio_device_output

    def setOutputDevice(self, device_id):
        print(f"Setting VLC audio output to {device_id}")
        self.vlcPlayer.audio_output_device_set(
            None, device_id)

    def vlcGymnastics(self):
        print("______Doing VLC gymnastics")
        print("______Setting volume to zero")
        self.setVolume(0)
        print("______Playing")
        self.vlcPlayer.play()
        print("______Setting volume to zero (again)")
        self.setVolume(0)

        wait_to_get_track_info_seconds = 1.5
        print(f"______sleeping for {wait_to_get_track_info_seconds}")
        sleep(wait_to_get_track_info_seconds)

        # pause, go back to the beginning,
        # set the volume back to something audible
        print("______Pausing")
        self.vlcPlayer.pause()
        print("______going back to beginning")
        self.vlcPlayer.set_position(0.0)
        wait_after_seek_0_seconds = 0.5
        print(f"______sleeping for {wait_after_seek_0_seconds}")
        sleep(wait_after_seek_0_seconds)
        print("______setting volume to settings")
        self.setDefaultVolumeFromSettings()

    def initPlayer(self, pathToTrack, withVlcGymnastics=False):
        # todo - set volume via settings.json!
        # settings_json = settings.get_settings()
        # output_route = settings_json.get("audio_output")

        print(f"initPlayer: Setting media to {pathToTrack}")
        media = self.instance.media_new(pathToTrack)
        self.sourcePath = pathToTrack
        self.vlcPlayer.set_media(media)

        if withVlcGymnastics:
            self.vlcGymnastics()

        # This audio device setting function doesn't seem to
        # work as expected...
        audio_output_device = self.getAudioOutput(settings.get_settings())
        # self.setOutputDevice(audio_output_device)
        # sleep(0.5)

    def getTrackLength(self):
        length_from_vlc = self.vlcPlayer.get_length() / 1000
        if length_from_vlc < 0:
            return 0
        else:
            return length_from_vlc

    def setVolume(self, value_0_to_100):
        print(f"setVolume: Setting volume to {value_0_to_100}")
        return self.vlcPlayer.audio_set_volume(value_0_to_100)

    def setDefaultVolumeFromSettings(self):
        print(
            f"setDefaultVolumeFromSettings: Setting volume to {self.initialVolumeFromSettings}")
        return self.setVolume(self.initialVolumeFromSettings)

    def triggerStart(self, pathToTrack, withPause=False):
        withVlcGymnastics = withPause
        self.initPlayer(pathToTrack, withVlcGymnastics)

        if not withPause:
            self.vlcPlayer.play()

        self.setDefaultVolumeFromSettings()

    def primeForStart(self, pathToTrack):
        print("priming vlc for start - loading track in PAUSED state")
        self.triggerStart(pathToTrack, withPause=True)

    def start(self, pathToTrack, syncTimestamp=None, master=False, slave=False):
        print(f"************* IN VLC START: master = {master}")
        try:

            if master or slave:
                self.vlcPlayer.play()
            else:
                self.triggerStart(pathToTrack)
                sleep(0.2)

            track_length_seconds = self.getTrackLength()

            # For whatever reason, audio_set_volume
            # will only work after the track has been playing for some short time
            self.setDefaultVolumeFromSettings()

            print("************** Playing on vlc...",
                  track_length_seconds)

            return track_length_seconds
        except Exception as e:
            print("ERROR: Could not start player... but audio may still be playing!")
            print("Why: ", e)
            print("returning position 0...")
            return str(0)

    def status(self, status):
        if self.vlcPlayer != None:
            print('status requested from VLC player!')
            try:

                frontend_friendly_status = ""

                # todo - map to simple dict
                if self.vlcPlayer.get_state() == State.Playing:
                    frontend_friendly_status = "Playing"

                if self.vlcPlayer.get_state() == State.Paused:
                    frontend_friendly_status = "Paused"

                # with the current frontend, the status must be the empty
                # string for the 'back' button to correctly navigate to the
                # track list
                #
                # if self.player.get_state() == State.Stopped:
                #     frontend_friendly_status = "Stopped"

                status["source"] = self.sourcePath
                status["playerState"] = frontend_friendly_status
                status["canControl"] = True
                status["position"] = self.getPosition()
                status["trackDuration"] = self.getTrackLength()
                status["error"] = ""
                status["paired"] = self.paired
                status["master_ip"] = self.masterIp
                status["volume"] = self.getVolume()
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
        player_state = self.vlcPlayer.get_state()

        print("Playpausing :: state -> ", str(player_state))

        if player_state == State.NothingSpecial:
            print("State.NothingSpecial - attempting to play")
            self.vlcPlayer.play()
        elif player_state == State.Stopped:
            print("State.Stopped - attempting to play")
            self.vlcPlayer.play()
        elif player_state == State.Paused:
            print("State.Paused - attempting to play")
            self.vlcPlayer.play()
        elif player_state == State.Playing:
            print("State.Playing - attempting to pause")
            self.vlcPlayer.pause()

    def playPause(self, syncTimestamp=None):
        print("Playpausing...")

        self.playPauseToggler()

        return self.getTrackLength()

    def setPaired(self, val, masterIp):
        self.paired = val
        self.masterIp = masterIp
        print('paired set to: ', val)
        print('master_ip set to: ', masterIp)

    def getPosition(self):
        return self.vlcPlayer.get_time() / 1000

    def seek(self, position0_to_100, syncTimestamp=None):

        position0_to_1 = float(position0_to_100) / 100
        print(f"Telling vlc player to seek to {position0_to_1}")
        self.vlcPlayer.set_position(position0_to_1)
        return self.getPosition()

    def pause(self):
        self.vlcPlayer.pause()

    def stop(self):
        print("Stopping...")
        self.vlcPlayer.stop()

    def mute(self):
        print("Muting...")
        self.vlcPlayer.audio_set_volume(0)

    def getVolume(self):
        return self.vlcPlayer.audio_get_volume()

    def volumeUp(self):
        self.vlcPlayer.audio_set_volume(self.vlcPlayer.audio_get_volume() + 5)

    def volumeDown(self, interval):
        idealStepSize = 2

        start_volume = self.vlcPlayer.audio_get_volume()

        step = idealStepSize

        current_volume = start_volume

        print("vlc downer: ", str(current_volume))
        # Vlc volume is between 0 and 100
        # below 10 is barely audible, ready for crossfading!
        if (current_volume <= 5 or interval == 0):
            # False =  we can't lower the volume anymore
            # False - no interval is specified, skip ahead now
            return False
        else:
            print(
                f"Ideal next step based on i: {interval} -> ", step)
            next_volume_step_down = current_volume - step
            if (next_volume_step_down < 0):
                next_volume_step_down = 0
            self.setVolume(next_volume_step_down)
            # True = the volume is not yet at a minimum
            return True

    def exit(self):

        if self.vlcPlayer:
            print("Stopping VLC")
            self.vlcPlayer.stop()
            self.setVolume(self.initialVolumeFromSettings)
            # self.__del__()
        else:
            return 1

    def __del__(self):
        attempt_to_cleanup_vlc = False

        if attempt_to_cleanup_vlc:
            try:
                player_release = self.vlcPlayer.release()
                print(f"Player release :: {player_release}")
            except Exception as e:
                print("Could not release player", e)

            try:
                instance_release = self.instance.release()
                print(f"Instance release :: {instance_release}")
            except Exception as e:
                print("Could not release instance", e)
        else:
            self.vlcPlayer.stop()
            print("Player stopped, setting volume back to 70")
            self.setVolume(self.initialVolumeFromSettings)

        print("VLC died")
