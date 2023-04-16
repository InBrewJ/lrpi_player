import mpv as libmpv
import settings
import os

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


def mpv_logger(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


class Mpv():
    _instance = None

    _mpv_standard_args = {
        "ytdl": False,
        "input_default_bindings": True,
        "input_vo_keyboard": False,
        # "log_handler": mpv_logger
    }

    # makes mpv.MPV a bonafide singleton
    # I'm not sure how the mpv library works under the hood
    # but, over extended LushRooms Pi usage,
    # to minimize thousands of 'mpv.MPV' which may
    # in turn spawn thousands of processes, make sure only
    # one mpv.MPV is created

    def __init__(self):
        raise RuntimeError(
            'For safety reasons, only call instance(), paused_instance() or destroy(), e.g. Mpv.destroy() - only one set of parentheses!')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new MpvInstance')
            cls._instance = libmpv.MPV(**cls._mpv_standard_args)
            cls._instance.set_loglevel('warn')
            cls._instance.wait_for_property('idle-active')
        return cls._instance

    @classmethod
    def paused_instance(cls):
        print('In order to create "paused_instance" :: destroying old instance')
        Mpv.destroy()
        if cls._instance is None:
            print('Creating new MpvInstance (PAUSED)')
            cls._instance = libmpv.MPV(**cls._mpv_standard_args, pause=True)
            cls._instance.set_loglevel('warn')
            print('waiting until idle-active...')
            cls._instance.wait_for_property('idle-active')
            print('returning paused instance...')
        return cls._instance

    @classmethod
    def destroy(cls):
        if cls._instance is not None:
            cls._instance.terminate()
            del cls._instance
            cls._instance = None


class MpvPlayer():
    def __init__(self):
        self.paired = False
        self.masterIp = ""
        self.sourcePath = ""
        settings_json = settings.get_settings()
        self.initialVolumeFromSettings: int = int(
            settings_json["audio_volume"])

    def validateTrackPath(self, pathToTrack):
        # todo: think about safely using this
        if not os.path.isfile(pathToTrack):
            raise Exception(f"{pathToTrack} is not a valid path")

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

        # must be set in /etc/asound.conf
        # see mpv_test/asoundrc_example_51
        for_hdmi = 'alsa/hdmiSurround51'
        for_jack = 'alsa/headphoneJackStereo'
        fallback = 'default'

        Mpv.instance()["audio-device"] = for_jack

    def initGymnastics(self):
        self.setDefaultVolumeFromSettings()

    def initPlayer(self, pathToTrack, withGymnastics=False):
        print(f"initPlayer: Setting media to {pathToTrack}")

        if withGymnastics:
            self.initGymnastics()

    def getTrackLength(self):
        # if it's not available - this will ALWAYS crash
        length_from_mpv = Mpv.instance()._get_property('duration')
        if length_from_mpv is None or length_from_mpv < 0:
            return 0
        else:
            return length_from_mpv

    def setVolume(self, value_0_to_100):
        print(f"setVolume: Setting volume to {value_0_to_100}")
        Mpv.instance().volume = value_0_to_100
        return value_0_to_100

    def setDefaultVolumeFromSettings(self):
        print(
            f"setDefaultVolumeFromSettings: Setting volume to {self.initialVolumeFromSettings}")
        return self.setVolume(self.initialVolumeFromSettings)

    def triggerStart(self, pathToTrack, withPause=False):
        initGymnastics = withPause
        self.initPlayer(pathToTrack, initGymnastics)

        if withPause:
            print(
                f"*** withPause = True, creating PAUSED instance, track {pathToTrack} ***")
            Mpv.paused_instance()
            Mpv.instance().play(pathToTrack)
            Mpv.instance().wait_until_paused()

        if not withPause:
            Mpv.paused_instance()
            Mpv.instance().play(pathToTrack)
            Mpv.instance().wait_until_paused()
            Mpv.instance()["pause"] = False
            print("****** WAITING UNTIL PLAYBACK BEGINS ******")
            Mpv.instance().wait_until_playing()

        self.setDefaultVolumeFromSettings()

    def primeForStart(self, pathToTrack):
        print("priming mpv for start - loading track in PAUSED state")
        self.sourcePath = pathToTrack
        # Note that mpv has a --pause staring option...
        # https://mpv.io/manual/master/#options-pause
        self.triggerStart(pathToTrack, withPause=True)

    def start(self, pathToTrack, master=False, slave=False):
        self.sourcePath = pathToTrack
        print(f"************* IN MPV START: master = {master} slave = {slave}")
        try:

            if master or slave:
                # we're in pairing mode, the player is already
                # primed and loaded. We just need to press play
                # todo: it's not yet primed and loaded for Mpv...
                print("*** Attempting to unpause playing after priming ***")
                Mpv.instance()["pause"] = False
                print("*** unpaused after priming, waiting until playing ***")
                Mpv.instance().wait_until_playing()
                print("*** playing... ***")
            else:
                self.triggerStart(pathToTrack)

            track_length_seconds = self.getTrackLength()

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
        if Mpv.instance() != None:
            print('status requested from MPV player!')
            try:

                frontend_friendly_status = ""

                # todo - map to simple dict
                if Mpv.instance()._get_property('core-idle') == False:
                    frontend_friendly_status = "Playing"

                if Mpv.instance()._get_property('pause') == True:
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
        Mpv.instance()['pause'] = not Mpv.instance()['pause']

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
        return Mpv.instance()._get_property('time-pos')

    def seek(self, position0_to_100):
        print(f"Telling mpv player to seek to {position0_to_100}%")
        Mpv.instance().seek(position0_to_100, reference='absolute-percent')
        return self.getPosition()

    def pause(self):
        Mpv.instance()['pause'] = True

    def stop(self):
        print("Stopping...")
        Mpv.instance().command('stop')

    def mute(self):
        print("Muting...")
        Mpv.instance().volume = 0

    def getVolume(self):
        return Mpv.instance()._get_property('volume')

    def volumeUp(self):
        pass

    def volumeDown(self, interval):
        idealStepSize = 2

        start_volume = self.getVolume()

        step = idealStepSize

        current_volume = start_volume

        print("mpv downer: ", str(current_volume))
        # mpv volume is between 0 and 100
        # On mpv, below 2 is barely audible, ready for crossfading!
        if (current_volume <= 2 or interval == 0):
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
        Mpv.destroy()

    def __del__(self):
        attempt_to_cleanup_mpv = False

        if attempt_to_cleanup_mpv:
            Mpv.destroy()
        else:
            Mpv.instance().stop()
            print("Player stopped, setting volume back to 70")
            self.setDefaultVolumeFromSettings()

        print("MPV died")
