import os
from os import uname, system
from time import sleep
import time
from time import perf_counter
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from Lighting import LushRoomsLighting
import ntplib  # pylint: disable=import-error
import pause  # pylint: disable=import-error
from pysrt import open as srtopen  # pylint: disable=import-error
from pysrt import stream as srtstream
import datetime
import calendar
import json
from threading import Thread

# utils

NTP_SERVER = 'uk.pool.ntp.org'


def findArm():

    return uname().machine == 'armv7l'


def getPlatformSpecificPlayer():
    # x86_64 for intel
    # armv7l for RPi3
    # aarch64 for RPi4 64bit
    # if none of the above, return omxplayer?
    machineType = uname().machine

    if machineType == 'x86_64':
        from VlcPlayer import VlcPlayer
        return VlcPlayer()

    if machineType == 'armv7l':
        from OmxPlayer import OmxPlayer
        return OmxPlayer()

    if machineType == 'aarch64':
        from MpvPlayer import MpvPlayer
        return MpvPlayer()

    raise Exception('Unsupported platform :: ' + machineType)


class LushRoomsPlayer():
    def __init__(self, playlist, basePath):
        print('Spawning LushRoomsPlayer')
        # TODO: store this in the player itself...
        self.audioPlayerType = "MPV"
        self.audioPlayer = getPlatformSpecificPlayer()
        self.lighting = LushRoomsLighting()
        self.basePath = basePath
        self.started = False
        self.playlist = playlist
        self.slaveCommandOffsetSeconds = 2
        self.slaveUrl = None
        self.status = {
            "source": "",
            "subsPath": "",
            "playerState": "",
            "canControl": "",
            "paired": False,
            "position": "",
            "trackDuration": "",
            "playerType": self.audioPlayerType,
            "playlist": self.playlist,
            "error": "",
            "slave_url": None,
            "master_ip": None
        }
        self.subs = None

    def getPlayerType(self):
        return self.audioPlayerType

    def isMaster(self):
        print("isMaster", self.audioPlayer.paired, self.status["master_ip"], self.audioPlayer.paired and (
            self.status["master_ip"] is None))
        # should this be based on "slave_ip" instead?
        return self.audioPlayer.paired and (self.status["master_ip"] is None)

    def isSlave(self):
        print("isSlave", self.audioPlayer.paired, self.status["master_ip"], self.audioPlayer.paired and (
            self.status["master_ip"] is None))

        return self.audioPlayer.paired and (self.status["master_ip"] is not None)

    def loadSubtitles(self, subsPath):
        if os.path.isfile(subsPath):
            start_time = time.time()
            print("Loading SRT file " + subsPath + " - " + str(start_time))
            subs = srtopen(subsPath)
            # subs = srtstream(subsPath)
            end_time = time.time()
            print("Finished loading SRT file " +
                  subsPath + " - " + str(end_time))
            print("Total time elapsed: " +
                  str(end_time - start_time) + " seconds")
            return subs
        else:
            print(
                f"Subtitle track file {subsPath} is not valid. Subtitles will NOT be loaded")
            return None

    # Returns the track_length_seconds

    def start(self, path, subs, subsPath, syncTime=None):
        self.audioPlayer.status(self.status)
        self.status["source"] = path
        self.status["subsPath"] = subsPath

        print("***************  player wrapper :: start  ********************")

        # in party mode - these subs need to be loaded _before_ playback start
        # on the slave. Otherwise audio will _always_ play 'Total time elapsed'
        # seconds BEHIND on the slave
        if not self.isMaster() and not self.isSlave():
            self.subs = self.loadSubtitles(subsPath)

        if self.isMaster():
            # if the command is 'start' we need to prime both players
            # so that we can simply press 'play' on the track
            # this ensures that tracks start at as close to the same
            # time as possible, minimising the 'springyhall reverb' effect

            print(f'Master :: priming master player subtitles from {subsPath}')
            self.subs = self.loadSubtitles(subsPath)
            print(f'Master :: priming master player with track {path}')
            self.audioPlayer.primeForStart(path)
            print(f'Master :: PLAYER IS PRIMED')
            print(f'Master :: priming slave player with track {path}')
            self.sendSlaveCommand('primeForStart')
            print('Master :: sending start command!')
            syncTime = self.sendSlaveCommand('start')
            self.pauseIfSync(syncTime)

        self.started = True
        # todo: replace this with the decorator from the Rpi3 branch
        t1_start = perf_counter()
        track_length_seconds = self.audioPlayer.start(
            path, self.isMaster(), self.isSlave())
        t1_stop = perf_counter()
        print("LushRooms audioPlayer start() took:", t1_stop - t1_start)

        try:
            self.lighting.start(self.audioPlayer, self.subs)
        except Exception as e:
            print('Lighting start failed: ', e)

        return track_length_seconds

    def playPause(self, syncTime=None):

        if self.isMaster():
            print('Master, sending playPause!')
            syncTime = self.sendSlaveCommand('playPause')
            self.pauseIfSync(syncTime)

        response = self.audioPlayer.playPause()

        try:
            self.lighting.playPause(self.getStatus()["playerState"])
        except Exception as e:
            print('Lighting playPause failed: ', e)

        return response

    def stop(self, syncTime=None):
        try:
            print('Stopping...')

            if self.isMaster():
                print('Master, sending stop!')
                syncTime = self.sendSlaveCommand('stop')
                self.pauseIfSync(syncTime)

            self.lighting.exit()
            self.audioPlayer.exit()

            return 0
        except Exception as e:
            print("stop failed: ", e)
            return 1

    def setPlaylist(self, playlist):
        self.playlist = playlist
        self.status["playlist"] = playlist

    def getPlaylist(self):
        if len(self.status["playlist"]):
            return self.status["playlist"]
        else:
            return False

    def resetLighting(self):
        if self.lighting:
            self.lighting.resetHUE()
            self.lighting.resetDMX()

    def fadeDown(self, path, interval, subs, subsPath, syncTimestamp=None):

        # Fade down the existing track

        print(f"fadeDown with interval {interval} seconds")

        self.status["interval"] = interval
        if self.isMaster():
            print('Master, sending fadeDown!')
            syncTime = self.sendSlaveCommand('fadeDown')
            self.pauseIfSync(syncTime)

        if syncTimestamp and self.isSlave():
            # this code is only called when isSlave is True?
            print('fadeDown - Slave - waiting until : ', syncTimestamp)
            self.pauseIfSync(syncTimestamp)

        if interval > 0:
            playerVolumeNow = self.audioPlayer.getVolume()
            idealStepSize = 2
            stepsNeeded = playerVolumeNow / idealStepSize
            sleepPerStep = interval / stepsNeeded
            while self.audioPlayer.volumeDown(interval):
                print(f"sleeping for {sleepPerStep}s until next volumeDown")
                sleep(sleepPerStep)

        # Player gymnastics
        # todo: we had to do this for vlc
        # maybe we don't need to do it for mpv?
        # This forces the volume to be audible
        # when the next track starts playing

        self.audioPlayer.mute()
        self.audioPlayer.pause()

        # Only set the volume back to the original value from
        # settings if the next track doesn't require both
        # master and slave to be primed. Setting the volume
        # here messes with the vlc gymnastics in VlcPlayer.py
        if not self.audioPlayer.paired:
            self.audioPlayer.setDefaultVolumeFromSettings()

        sleep(0.2)

        self.audioPlayer.exit()
        self.lighting.exit()

        # Then play the next track!
        if not self.isSlave():
            return self.start(path, subs, subsPath)
        else:
            return 0

    def seek(self, position, syncTimestamp=None):
        if self.started:

            if self.isMaster():
                print('Master, sending seek!')
                syncTime = self.sendSlaveCommand('seek', position)
                self.pauseIfSync(syncTime)

            newPos = self.audioPlayer.seek(position)
            self.lighting.seek(newPos)
            return newPos

    def getStatus(self):
        self.status["slave_url"] = self.slaveUrl
        return self.audioPlayer.status(self.status)

    # Pair methods called by the master

    def pairAsMaster(self, slaveHostname):
        response = os.system("ping -c 1 " + slaveHostname)
        if response == 0:
            print(slaveHostname, 'is up!')
            self.slaveUrl = "http://" + slaveHostname
            print("slaveUrl: ", self.slaveUrl)
            statusRes = urllib.request.urlopen(
                self.slaveUrl + "/status").read()
            print("status: ", statusRes)
            if statusRes:
                print('Attempting to enslave: ' + slaveHostname)
                enslaveRes = urllib.request.urlopen(
                    self.slaveUrl + "/enslave").read()
                print('res from enslave: ', enslaveRes)
                master_ip = None
                self.audioPlayer.setPaired(True, master_ip)

        else:
            print(slaveHostname, 'is down! Cannot pair!')
            return 1

        return 0

    def unpairAsMaster(self):
        print("slaveUrl: ", self.slaveUrl)
        statusRes = urllib.request.urlopen(self.slaveUrl + "/status").read()
        print("status: ", statusRes)
        if statusRes:
            print('Attempting to free the slave: ' + self.slaveUrl)
            freeRes = urllib.request.urlopen(self.slaveUrl + "/free").read()
            print('res from free: ', freeRes)
            if freeRes:
                self.audioPlayer.setPaired(False, None)
            else:
                print('Error freeing the slave')
                return 1

        return 0

    # Methods called by the slave

    def setPairedAsSlave(self, val, masterIp):
        self.audioPlayer.setPaired(val, masterIp)

    def free(self):
        if self.audioPlayer.paired:
            self.audioPlayer.setPaired(False, None)
            self.audioPlayer.exit()
            return 0

    def getLocalTimestamp(self):
        return datetime.datetime.now()

    def pauseIfSync(self, syncTimestamp=None):
        print('synctime in LushRoomsPlayer: ',
              syncTimestamp, " :: ", syncTimestamp)
        if syncTimestamp:
            print("*" * 30)
            print("** syncTimestamp found for pairing mode!")
            print(
                f"Pausing next LushRoomsPlayer command until {syncTimestamp}, time now is {self.getLocalTimestamp()}")
            print("*" * 30)
            pause.until(syncTimestamp)

    # When this player is enslaved, map the status of the
    # master to a method

    def commandFromMaster(self, masterStatus, command, position, startTime):

        localTimestamp = self.getLocalTimestamp()

        print('commandFromMaster :: currentUnixTimestamp (local on pi: )',
              localTimestamp)

        res = 1
        if self.audioPlayer.paired:

            print('command from master: ', command)
            print('master status: ', masterStatus)
            print('startTime: ', startTime)

            print("*" * 30)
            print(f"SLAVE COMMAND RECEIVED {command}, events sync at: ",
                  startTime)
            print("*" * 30)

            # All commands are mutually exclusive

            # We do not have a startTime for primeForStart, it is the precursor to
            # all other waits. The master will wait patiently until the slave
            # has been primed
            if command == "primeForStart":
                pathToAudioTrack = masterStatus["source"]
                pathToSubsTrack = masterStatus["subsPath"]
                print(
                    f'Slave :: priming slave player subtitles from {pathToSubsTrack}')
                self.subs = self.loadSubtitles(pathToSubsTrack)
                print(
                    f'Slave :: priming slave player with track {pathToAudioTrack}')
                self.audioPlayer.primeForStart(pathToAudioTrack)
                print(f'Slave :: PLAYER IS PRIMED')
            else:
                self.pauseIfSync(startTime)

            if command == "start":
                self.start(
                    masterStatus["source"],
                    None,
                    masterStatus["subsPath"],
                    startTime
                )

            if command == "playPause":
                self.playPause()

            if command == "stop":
                self.stop()

            if command == "seek":
                self.seek(position)

            if command == "fadeDown":
                self.fadeDown(masterStatus["source"],
                              masterStatus["interval"],
                              None,
                              masterStatus["subsPath"])
            res = 0

        else:
            print('Not paired, cannot accept master commands')
            res = 1

        return res

    # When this player is acting as master, send commands to
    # the slave with an 'eventSyncTime' timestamp

    def sendSlaveCommand(self, command, position=None):
        if self.audioPlayer.paired:
            print('sending command to slave: ', command)
            try:

                localTimestamp = self.getLocalTimestamp()

                print('currentUnixTimestamp (local on pi: )',
                      localTimestamp)
                self.eventSyncTime = localTimestamp + \
                    datetime.timedelta(0, self.slaveCommandOffsetSeconds)
                print("*" * 30)
                print(f"MASTER COMMAND SENT {command}, events sync at: ",
                      self.eventSyncTime)
                print("*" * 30)

                # send the event sync time to the slave...
                postFields = {
                    'command': str(command),
                    'position': str(position),
                    'master_status': self.getStatus(),
                    'sync_timestamp': str(self.eventSyncTime)
                }

                def slaveRequest():
                    slaveRes = requests.post(
                        self.slaveUrl + '/command', json=postFields)
                    print('command from slave, res: ', slaveRes.json)

                if command == "primeForStart":
                    # we only want the primeForStart command to be blocking.
                    # This way we can be absolutely sure that the play button
                    # on the slave player is ready to be pushed...
                    slaveRequest()
                else:
                    # The slave might take an arbitrary amount of time to complete
                    # the command (e.g. fadeDown, lots of sleeps).
                    # Therefore, start it in a thread
                    # we don't often care about the result
                    Thread(target=slaveRequest).start()

                return self.eventSyncTime

            except Exception as e:
                print(f'Could not send {command} to slave {self.slaveUrl}')
                print('Why: ', e)

        else:
            print('Not paired, cannot send commands to slave')

        return None

    def exit(self):
        self.audioPlayer.exit()

    # mysterious Python destructor...

    def __del__(self):
        self.audioPlayer.__del__()
        print("LRPlayer died")
