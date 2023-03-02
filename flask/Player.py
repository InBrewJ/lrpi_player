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
    from OmxPlayer import OmxPlayer
else:
    from VlcPlayer import VlcPlayer


# todo:
# VlcPlayer should also be singleton?

class LushRoomsPlayer():
    def __init__(self, playlist, basePath):
        # TODO BANANA: arch will differ here
        # Additionally, Omxplayer likely won't work on a Banana - favour vlc going forward? Omxplayer is also likely NOT suited for the RPi4 (deprecation note...)
        if False:
            # we're likely on a 'Pi
            self.playerType = "OMX"
            print('Spawning omxplayer')
            # self.player = OmxPlayer()
        else:
            # we're likely on a desktop
            print('You are likely on a desktop / NOT a RPi 2 or 3!')
            print('Therefore, spawning vlc player')
            self.playerType = "VLC"
            self.player = VlcPlayer()

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
            "playerType": self.playerType,
            "playlist": self.playlist,
            "error": "",
            "slave_url": None,
            "master_ip": None
        }
        self.subs = None

    def getPlayerType(self):
        return self.playerType

    def isMaster(self):
        print("isMaster", self.player.paired, self.status["master_ip"], self.player.paired and (
            self.status["master_ip"] is None))
        # should this be based on "slave_ip" instead?
        return self.player.paired and (self.status["master_ip"] is None)

    def isSlave(self):
        print("isSlave", self.player.paired, self.status["master_ip"], self.player.paired and (
            self.status["master_ip"] is None))

        return self.player.paired and (self.status["master_ip"] is not None)

    # Returns the track_length_seconds
    def start(self, path, subs, subsPath, syncTime=None):
        self.player.status(self.status)
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
            self.player.primeForStart(path)
            print(f'Master :: priming slave player with track {path}')
            self.sendSlaveCommand('primeForStart')
            print('Master :: sending start command!')
            syncTime = self.sendSlaveCommand('start')
            self.pauseIfSync(syncTime)

        self.started = True
        track_length_seconds = self.player.start(
            path, syncTime, self.isMaster(), self.isSlave())

        try:
            self.lighting.start(self.player, subs)
        except Exception as e:
            print('Lighting failed: ', e)

        return track_length_seconds

    def playPause(self, syncTime=None):

        if self.isMaster():
            print('Master, sending playPause!')
            syncTime = self.sendSlaveCommand('playPause')
            self.pauseIfSync(syncTime)

        response = self.player.playPause(syncTime)

        try:
            print('In Player: ', id(self.player))
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
            self.player.exit(syncTime)

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
            playerVolumeNow = self.player.getVolume()
            idealStepSize = 2
            stepsNeeded = playerVolumeNow / idealStepSize
            sleepPerStep = interval / stepsNeeded
            while self.player.volumeDown(interval):
                print(f"sleeping for {sleepPerStep}s until next volumeDown")
                sleep(sleepPerStep)

        # VLC gymnastics
        # This forces the volume to be audible
        # when the next track starts playing

        self.player.mute()
        self.player.pause()
        self.player.setDefaultVolumeFromSettings()

        sleep(0.2)

        self.player.exit()
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

            newPos = self.player.seek(position, syncTimestamp)
            self.lighting.seek(newPos)
            return newPos

    def getStatus(self):
        self.status["slave_url"] = self.slaveUrl
        return self.player.status(self.status)

    # Pair methods called by the master

    def pairAsMaster(self, hostname):
        response = os.system("ping -c 1 " + hostname)
        if response == 0:
            print(hostname, 'is up!')
            self.slaveUrl = "http://" + hostname
            print("slaveUrl: ", self.slaveUrl)
            statusRes = urllib.request.urlopen(
                self.slaveUrl + "/status").read()
            print("status: ", statusRes)
            if statusRes:
                print('Attempting to enslave: ' + hostname)
                enslaveRes = urllib.request.urlopen(
                    self.slaveUrl + "/enslave").read()
                print('res from enslave: ', enslaveRes)
                self.player.setPaired(True, None)

        else:
            print(hostname, 'is down! Cannot pair!')
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
                self.player.setPaired(False, None)
            else:
                print('Error freeing the slave')
                return 1

        return 0

    # Methods called by the slave

    def setPairedAsSlave(self, val, masterIp):
        self.player.setPaired(val, masterIp)

    def free(self):
        if self.player.paired:
            self.player.setPaired(False, None)
            self.player.exit()
            return 0

    # When this player is enslaved, map the status of the
    # master to a method

    def pauseIfSync(self, syncTimestamp=None):
        print('synctime in LushRoomsPlayer: ', ctime(syncTimestamp))
        if syncTimestamp:
            print("*" * 30)
            print("** syncTimestamp found for pairing mode!")
            print(
                f"Pausing next LushRoomsPlayer command until {ctime(syncTimestamp)}")
            print("*" * 30)
            pause.until(syncTimestamp)

    def commandFromMaster(self, masterStatus, command, position, startTime):
        res = 1
        if self.player.paired:

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
                self.player.primeForStart(pathToTrack)
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
    # the slave with a 'start' timestamp

    def sendSlaveCommand(self, command, position=None):
        if self.player.paired:
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
                # if we don't get a response don't try and trigger the event!
                self.player.status(self.status)
                postFields = {
                    'command': str(command),
                    'position': str(position),
                    'master_status': self.getStatus(),
                    'sync_timestamp': self.eventSyncTime
                }

                # The slave might take an arbitrary amount of time to complete
                # the command (e.g. fadeDown, lots of sleeps).
                # Therefore, start it in a thread
                # we don't often care about the result

                def slaveRequest():
                    slaveRes = requests.post(
                        self.slaveUrl + '/command', json=postFields)
                    print('command from slave, res: ', slaveRes)

                if command == "primeForStart":
                    # we only want the primeForStart command to be blocked
                    # this way we can be absolutely sure that the play button
                    # on the slave player is ready to be pushed...
                    slaveRequest()
                else:
                    Thread(target=slaveRequest).start()

                return self.eventSyncTime

            except Exception as e:
                print(f'Could not send {command} to slave {self.slaveUrl}')
                print('Why: ', e)

        else:
            print('Not paired, cannot send commands to slave')

        return None

    def exit(self):
        self.player.exit()

    # mysterious Python destructor...

    def __del__(self):
        self.player.__del__()
        print("LRPlayer died")
