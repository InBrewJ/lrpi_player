import os
from os import uname, system
from time import sleep
import time
import urllib.request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib import parse
import requests
import ntplib  # pylint: disable=import-error
from time import ctime
import pause  # pylint: disable=import-error
from pysrt import open as srtopen  # pylint: disable=import-error
from pysrt import stream as srtstream
import datetime
import calendar
import json
from threading import Thread


def getLocalTimestamp():
    return calendar.timegm(
        datetime.datetime.now().timetuple())


now_unix = getLocalTimestamp()

# if uses in pause.until in DST, now_unix will be an hour ahead. Gah
print(f"time now unix ts: {now_unix}")

now_datetime = datetime.datetime.now()

plus_2_secs = now_datetime + datetime.timedelta(0, 2)

print(f"Pausing until {str(plus_2_secs)}")

pause.until(plus_2_secs)
