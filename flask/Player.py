import os
from os import uname, system
from time import sleep
import time
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from Lighting import LushRoomsLighting
import ntplib  # pylint: disable=import-error
from time import ctime
import pause  # pylint: disable=import-error
from pysrt import open as srtopen  # pylint: disable=import-error
from pysrt import stream as srtstream
import datetime
import calendar
import json
from threading import Thread

# utils

# NTP_SERVER = 'ns1.luns.net.uk'
NTP_SERVER = 'uk.pool.ntp.org'


def findArm():
    return uname().machine == 'armv7l'


if False:
    # For Rpi 3 system
    from OmxPlayer import OmxPlayer
    # For systems where VLC decodes high bitrate audio fast enough
    from VlcPlayer import VlcPlayer
else:
    # For now, for Rpi 4
    from MpvPlayer import MpvPlayer


class LushRoomsPlayer():
    def __init__(self, playlist, basePath):
        print('Spawning LushRoomsPlayer')
        self.audioPlayerType = "MPV"
        self.audioPlayer = MpvPlayer()
        self.lighting = LushRoomsLighting()
        self.basePath = basePath
        self.started = False
        self.playlist = playlist
        self.slaveCommandOffset = 2.7  # seconds
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

    # Returns the track_length_seconds
    def start(self, path, subs, subsPath, syncTime=None):
        self.audioPlayer.status(self.status)
        self.status["source"] = path
        self.status["subsPath"] = subsPath

        print("***************  player wrapper :: start  ********************")

        if os.path.isfile(subsPath):
            start_time = time.time()
            print("Loading SRT file " + subsPath + " - " + str(start_time))
            subs = srtopen(subsPath)
            #subs = srtstream(subsPath)
            end_time = time.time()
            print("Finished loading SRT file " +
                  subsPath + " - " + str(end_time))
            print("Total time elapsed: " +
                  str(end_time - start_time) + " seconds")

        if self.isMaster():
            # if the command is 'start' we need to prime both players
            # so that we can simply press 'play' on the track
            # this ensures that tracks start at as close to the same
            # time as possible, minimising the 'springhall reverb' effect

            print(f'Master :: priming master player with track {path}')
            self.audioPlayer.primeForStart(path)
            print(f'Master :: priming slave player with track {path}')
            self.sendSlaveCommand('primeForStart')
            print('Master :: sending start command!')
            syncTime = self.sendSlaveCommand('start')
            self.pauseIfSync(syncTime)

        self.started = True
        track_length_seconds = self.audioPlayer.start(
            path, self.isMaster(), self.isSlave())

        try:
            self.lighting.start(self.audioPlayer, subs)
        except Exception as e:
            print('Lighting failed: ', e)

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
            pause.until(syncTimestamp)

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

    def pauseIfSync(self, syncTimestamp=None):
        print('synctime in LushRoomsPlayer: ', ctime(syncTimestamp))
        if syncTimestamp:
            print("*" * 30)
            print("** syncTimestamp found for pairing mode!")
            print(
                f"Pausing next LushRoomsPlayer command until {ctime(syncTimestamp)}")
            print("*" * 30)
            pause.until(syncTimestamp)

    # When this player is enslaved, map the status of the
    # master to a method

    def commandFromMaster(self, masterStatus, command, position, startTime):
        res = 1
        if self.audioPlayer.paired:

            print('command from master: ', command)
            print('master status: ', masterStatus)
            print('startTime: ', startTime)

            print("*" * 30)
            print(f"SLAVE COMMAND RECEIVED {command}, events sync at: ", ctime(
                startTime))
            print("*" * 30)

            # All commands are mutually exclusive

            if command == "primeForStart":
                pathToTrack = masterStatus["source"]
                print(
                    f'Slave :: priming slave player with track {pathToTrack}')
                self.audioPlayer.primeForStart(pathToTrack)
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

                localTimestamp = calendar.timegm(
                    datetime.datetime.now().timetuple())

                print('currentUnixTimestamp (local on pi: )', localTimestamp)
                self.eventSyncTime = localTimestamp + self.slaveCommandOffset
                print("*" * 30)
                print(f"MASTER COMMAND SENT {command}, events sync at: ", ctime(
                    self.eventSyncTime))
                print("*" * 30)

                # send the event sync time to the slave...
                postFields = {
                    'command': str(command),
                    'position': str(position),
                    'master_status': self.getStatus(),
                    'sync_timestamp': self.eventSyncTime
                }

                def slaveRequest():
                    slaveRes = requests.post(
                        self.slaveUrl + '/command', json=postFields)
                    print('command from slave, res: ', slaveRes)

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
