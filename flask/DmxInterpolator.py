from pysrt import SubRipFile, SubRipItem, SubRipTime # pylint: disable=import-error
from numpy import array, ones, zeros, full # pylint: disable=import-error

VERBOSE=False

class DmxInterpolator():
    def __init__(self):
        self.start_frame = None
        self.target_frame = None
        self.start_time = None
        self.target_time = None
        self.duration = None
        self.running = False
        self.num_channels = None
        self.twiddle = 0.4
        self.min_interpolation_window = 0.05

    def srt_to_seconds(self, t):
        block, milliseconds = str(t).split(",")
        hours, minutes, seconds = block.split(":")
        u_ts = (int(seconds) + int(minutes)*60 + int(hours)*60*60 + int(milliseconds)/1000.0)
        # print("converted to seconds: ", u_ts)
        return u_ts

    def srt_to_array(self, f):
        # print("converting frame: ", f)
        scope,items = f[0:len(f)-1].split("(")
        return array(items.split(",")).astype(int)   

    def start(
        self,
        start_frame,
        start_time,
        target_frame,
        target_time
    ):

        self.start_time = self.srt_to_seconds(start_time)
        self.target_time = self.srt_to_seconds(target_time)
        self.duration = self.target_time - self.start_time

        if self.duration > self.min_interpolation_window:
            self.start_frame = self.srt_to_array(start_frame)
            self.target_frame = self.srt_to_array(target_frame)
            self.start_time = self.srt_to_seconds(start_time)
            self.target_time = self.srt_to_seconds(target_time)
            self.num_channels = len(self.start_frame)
            self.running = True
            if VERBOSE:
                print("Interpolator starting with duration: ", self.duration)
                print("Starts at: ", self.start_time)
                print("Ends at: ", self.target_time)
                print("Running ", self.running)

    def isRunning(self):
        return self.running

    def clear(self):
        self.start_frame = None
        self.start_time = None
        self.target_time = None
        self.duration = None
        self.running = False
        self.num_channels = None

    def findNextEvent(
        self,
        thisI,
        subtitle
    ):
        # Look for the next DMX event
        # If there isn't one, don't start the interpolator

        nextI = thisI + 1
        lenSubs = len(subtitle)

        while nextI < lenSubs and not self.running:
            if subtitle[nextI].text.find("DMX", 0, 5) > -1 and subtitle[thisI].text.find("DMX", 0, 5) > -1:
                if VERBOSE:
                    print("Interpolation event found!")
                    print('From frame: ', subtitle[thisI].text)
                    print('at time: ', subtitle[thisI].start)
                    print('TO frame: ', subtitle[nextI].text)
                    print('until time: ', subtitle[nextI].start)
                
                self.start(
                    subtitle[thisI].text,
                    subtitle[thisI].start,
                    subtitle[nextI].text,
                    subtitle[nextI].start
                )
            nextI += 1

    # NB: this is linear interpolation only!       

    def getInterpolatedFrame(self, current_time):
        # Calculate the interpolated DMX frame
        # ct is 'current time'
        ct = self.srt_to_seconds(current_time)
     
        # max() is used here to account for what could
        # be rounding errors
        normalized_ct = max(0, ct - self.start_time)
        if VERBOSE:
            print('normalized ct: ', normalized_ct)
        else:
            print('i')

        # frame_diff = self.target_frame[0] - self.start_frame[0]
        # val = int(((normalized_ct/self.duration)*frame_diff) + self.start_frame[0])
        
        # Above, the basic method for interpolating a single DMX frame.
        # Below, a lambda that does the same thing but for all DMX channels

        interpolated_frame = map(lambda sf, tf: int(((normalized_ct/self.duration)*(tf-sf))) + sf, self.start_frame, self.target_frame)


        if (ct >= self.target_time - self.twiddle):
            self.running = False
            self.clear()
            if VERBOSE:
                print("Target reached!")
                print("target frame: ", self.target_frame)
            return self.target_frame      
        else:
            iFrame = list(interpolated_frame)
            if VERBOSE:
                print("from interpolation: ", iFrame)
            return iFrame
        