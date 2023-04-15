from time import sleep
import mpv
import settings

# mpv binding repo (for v0.5.2 - this version is most easily installed on Rpi4 Bullseye with odd old Debian repo listings)
# https://github.com/jaseg/python-mpv/tree/v0.5.2
# libmpv docs
# https://mpv.io/manual/master/
# tested on Rpi 4 with mpv 0.32.0
# https://github.com/mpv-player/mpv/tree/release/0.32


# to install mpv on Rpi
# sudo apt install mpv libmpv-dev python3-mpv

# to install on Ubuntu host
# sudo apt install mpv libmpv-dev python3-mpv


class MpvInstance():
    _instance = None

    # makes mpv.MPV a bonafide singleton
    # I'm not sure how the mpv library works under the hood
    # but, over extended LushRooms Pi usage,
    # to minimize thousands of 'mpv.MPV' which may
    # in turn spawn thousands of processes, make sure only
    # one mpv.MPV is created
    def __init__(self):
        raise RuntimeError('For safety reasons, call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new instance')
            cls._instance = mpv.MPV(ytdl=False, input_default_bindings=True,
                                    input_vo_keyboard=False)
        return cls._instance


class MpvPlayer():
    def __init__(self):
        self.instance = MpvInstance.instance()
        self.mpvPlayer = self.instance
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
        print(f"Setting mpv audio output to {device_id}")

        # something related to this:
        # https://raspberrypi.stackexchange.com/a/127517
        #
        # test on command line first!
        #
        # host of resources here, too
        # https://elinux.org/New_Pi_OS_sound_trouble_shooting

        self.mpvPlayer.audio_output_device_set(
            None, device_id)

    def initGymnastics(self):
        self.setDefaultVolumeFromSettings()

    def initPlayer(self, pathToTrack, withGymnastics=False):
        print(f"initPlayer: Setting media to {pathToTrack}")
        # self.mpvPlayer.play(pathToTrack)

        if withGymnastics:
            self.initGymnastics()

    def getTrackLength(self):
        # if it's not available - this will ALWAYS crash
        length_from_mpv = self.mpvPlayer._get_property('duration')
        if length_from_mpv is None or length_from_mpv < 0:
            return 0
        else:
            return length_from_mpv

    def setVolume(self, value_0_to_100):
        print(f"setVolume: Setting volume to {value_0_to_100}")
        self.mpvPlayer.volume = value_0_to_100
        return value_0_to_100

    def setDefaultVolumeFromSettings(self):
        print(
            f"setDefaultVolumeFromSettings: Setting volume to {self.initialVolumeFromSettings}")
        return self.setVolume(self.initialVolumeFromSettings)

    def triggerStart(self, pathToTrack, withPause=False):
        initGymnastics = withPause
        self.initPlayer(pathToTrack, initGymnastics)

        if not withPause:
            self.mpvPlayer.play(pathToTrack)
            self.mpvPlayer.wait_until_playing()

        self.setDefaultVolumeFromSettings()

    def primeForStart(self, pathToTrack):
        print("priming mpv for start - loading track in PAUSED state")
        # Note that mpv has a --pause staring option...
        # https://mpv.io/manual/master/#options-pause
        self.triggerStart(pathToTrack, withPause=True)

    def start(self, pathToTrack, master=False, slave=False):
        print(f"************* IN MPV START: master = {master} slave = {slave}")
        try:

            if master or slave:
                # we're in pairing mode, the player is already
                # primed and loaded. We just need to press play
                self.mpvPlayer.play()
            else:
                self.triggerStart(pathToTrack)
                # when we're not in pairing mode, we need to wait
                # a little bit for the track to start playing
                # so that getTrackLength will return a non zero figure
                sleep(0.2)

            track_length_seconds = self.getTrackLength()

            # For whatever reason, audio_set_volume
            # will only work after the track has been playing for some short time
            self.setDefaultVolumeFromSettings()

            print("************** Playing on mpv...",
                  track_length_seconds)

            return track_length_seconds
        except Exception as e:
            print("ERROR: Could not start player... but audio may still be playing!")
            print("Why: ", e)
            print("returning position 0...")
            return str(0)

    def status(self, status):
        if self.mpvPlayer != None:
            print('status requested from MPV player!')
            try:

                frontend_friendly_status = ""

                # todo - map to simple dict
                if self.mpvPlayer._get_property('core-idle') == False:
                    frontend_friendly_status = "Playing"

                if self.mpvPlayer._get_property('pause') == True:
                    frontend_friendly_status = "Paused"

                # with the current table ui implementation, the status must be the empty
                # string for the 'back' button to correctly navigate to the
                # track list

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
        self.mpvPlayer['pause'] = not self.mpvPlayer['pause']

    def playPause(self):
        print("Playpausing...")

        self.playPauseToggler()

        return self.getTrackLength()

    def setPaired(self, val, masterIp):
        self.paired = val
        self.masterIp = masterIp
        print('paired set to: ', val)
        print('master_ip set to: ', masterIp)

    def getPosition(self):
        return self.mpvPlayer._get_property('time-pos')

    def seek(self, position0_to_100):
        print(f"Telling mpv player to seek to {position0_to_100}%")
        self.mpvPlayer.seek(position0_to_100, reference='absolute-percent')
        return self.getPosition()

    def pause(self):
        self.mpvPlayer.pause()

    def stop(self):
        print("Stopping...")
        self.mpvPlayer.command('stop')

    def mute(self):
        print("Muting...")
        self.mpvPlayer.audio_set_volume(0)

    def getVolume(self):
        return self.mpvPlayer._get_property('volume')

    def volumeUp(self):
        pass

    def volumeDown(self, interval):
        idealStepSize = 2

        start_volume = self.mpvPlayer.audio_get_volume()

        step = idealStepSize

        current_volume = start_volume

        print("mpv downer: ", str(current_volume))
        # mpv volume is between 0 and 100
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

        if self.mpvPlayer:
            print("Stopping MPV")
            self.mpvPlayer.stop()
            self.setVolume(self.initialVolumeFromSettings)
            # self.__del__()
        else:
            return 1

    def __del__(self):
        attempt_to_cleanup_mpv = False

        if attempt_to_cleanup_mpv:
            try:
                player_release = self.mpvPlayer.release()
                print(f"Player release :: {player_release}")
            except Exception as e:
                print("Could not release player", e)

            try:
                instance_release = self.instance.release()
                print(f"Instance release :: {instance_release}")
            except Exception as e:
                print("Could not release instance", e)
        else:
            self.mpvPlayer.stop()
            print("Player stopped, setting volume back to 70")
            self.setVolume(self.initialVolumeFromSettings)

        print("MPV died")
