import os
from os import uname, system
from time import sleep
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
from Lighting import LushRoomsLighting
import ntplib # pylint: disable=import-error
from time import ctime
import pause # pylint: disable=import-error
import json

# utils

NTP_SERVER = 'ns1.luns.net.uk'

def findArm(): 
    return uname().machine == 'armv7l' 

if findArm():
    from OmxPlayer import OmxPlayer
else: 
    from VlcPlayer import VlcPlayer

class LushRoomsPlayer():
    def __init__(self, playlist, basePath):
        if uname().machine == 'armv7l':
            # we're likely on a 'Pi
            self.playerType = "OMX"
            print('Spawning omxplayer')
            self.player = OmxPlayer()
        else:
            # we're likely on a desktop
            print('Spawning vlc player')
            self.playerType = "VLC"
            self.player = VlcPlayer()

        self.lighting = LushRoomsLighting()
        self.basePath = basePath
        self.started = False
        self.playlist = playlist
        self.slaveCommandOffset = 2.0 # seconds
        self.eventSyncTime = None
        self.slaveUrl = None
        self.status = {
            "source" : "",
            "subsPath" : "",
            "playerState" : "",
            "canControl" : "",
            "paired" : False,
            "position" : "",
            "trackDuration" : "",
            "playerType": self.playerType,
            "playlist": self.playlist,
            "error" : "",
            "slave_url": None
        }
        self.subs = None
 
    def getPlayerType(self):
        return self.playerType    

    # Returns the current position in secoends
    def start(self, path, subs, subsPath):
        self.player.status(self.status) 
        self.status["source"] = path
        self.status["subsPath"] = subsPath

        commandMustSyncSlave = self.player.paired and self.status["master_ip"] is None and self.eventSyncTime is not None

        isMaster = self.player.paired and self.status["master_ip"] is None

        if commandMustSyncSlave:
            # wait until the sync time to fire everything off
            print('Slave: Syncing start!')  

        if isMaster:
            print('Master, sending start!')
            self.sendSlaveCommand('start')

        self.started = True
        response = self.player.start(path)

        try:
            print('In Player: ', id(self.player))
            self.lighting.start(self.player, subs) 
        except Exception as e:
            print('Lighting failed: ', e)  

        return response

    def playPause(self):
        response = self.player.playPause()
        try:
            print('In Player: ', id(self.player))
            self.lighting.playPause(self.getStatus()["playerState"]) 
        except Exception as e:
            print('Lighting failed: ', e)
        return response

    def stop(self):
        try:
            print('Stopping...')
            self.lighting.exit()
            self.player.exit()
            return 0
        except Exception as e:
            print("stop e: ", e)
            return 1

    def setPlaylist(self, playlist):
        self.playlist = playlist
        self.status["playlist"] = playlist
 
    def getPlaylist(self):
        if len(self.status["playlist"]):
            return self.status["playlist"]
        else:
            return False

    def next(self):
        print("Skipping forward...")

    def previous(self):
        print("Skipping back...")

    def fadeDown(self, path, interval, subs, subsPath):
        if interval > 0: 
            while self.player.volumeDown(interval):
                sleep(1.0/interval)
        self.player.exit() 
        self.lighting.exit() 
        response = self.player.start(path)
        self.status["subsPath"] = subsPath
        try:
            print('In Player: ', id(self.player))
            self.lighting.start(self.player, subs) 
        except Exception as e:
            print('Lighting failed: ', e) 

        return response

    def seek(self, position):
        if self.started:
            self.lighting.seek()
            return self.player.seek(position)

    def getStatus(self):
        return self.player.status(self.status)

    # Pair method called by the master

    def pairAsMaster(self, hostname): 
        response = os.system("ping -c 1 " + hostname)
        if response == 0:
            print(hostname, 'is up!')
            self.slaveUrl = "http://" + hostname
            print("slaveUrl: ", self.slaveUrl)
            statusRes = urllib.request.urlopen(self.slaveUrl + "/status").read()
            print("status: ", statusRes)
            if statusRes:
                print('Attempting to enslave: ' + hostname)
                enslaveRes = urllib.request.urlopen(self.slaveUrl + "/enslave").read()
                print('res from enslave: ', enslaveRes)
                self.player.setPaired(True, None)

        else:
            print(hostname, 'is down! Cannot pair!')

        return 0

    # Method called by the slave

    def setPairedAsSlave(self, val, masterIp): 
        self.player.setPaired(val, masterIp)

    def unPair(self):
        if self.player.paired:
            self.player.setPaired(False, None)
            self.player.exit()

    # When this player is enslaved, map the status of the 
    # master to a method

    def commandFromMaster(self, masterStatus, command, startTime):
        if self.player.paired:
            print('command from master: ', command)
            print('Master status: ', masterStatus)

        else:
            print('Not paired, cannot accept master commands')

    # When this player is acting as master, send commands to 
    # the slave with a 'start' timestamp

    def sendSlaveCommand(self, command):
        if self.player.paired:
            print('sending command to slave: ', command)
            c = ntplib.NTPClient()
            try:
                # tx_time is a unix timestamp
                # this, among a few other things, means 'party mode'
                # is only available on the 'Pi'/other unix like systems
                response = c.request(NTP_SERVER)
                print('\n' + 30*'-')
                print('ntp time: ', ctime(response.tx_time))
                print('ntp time raw: ', response.tx_time)
                print(30*'-' + '\n')
                self.eventSyncTime = response.tx_time + self.slaveCommandOffset
                print('events sync at: ', self.eventSyncTime)


                # send the event sync time to the slave...
                # if we don't get a response don't try and trigger the event!
                self.player.status(self.status)
                postFields = { \
                    'command': str(command), \
                    'master_status': self.getStatus(), \
                    'sync_timestamp': self.eventSyncTime \
                }
                slaveRes = requests.post(self.slaveUrl + '/command', json=postFields)
                print('command from slave, res: ', slaveRes)

                pause.until(self.eventSyncTime)
                print('After pause!')

                
            except Exception as e:
                print('Could not get ntp time!')
                print('Why: ', e)
            

        else:
            print('Not paired, cannot send commands to slave')


    def exit(self):
        self.player.exit()

    # mysterious Python destructor...

    def __del__(self):
        self.player.__del__()
        print("LRPlayer died")