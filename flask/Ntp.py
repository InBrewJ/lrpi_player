import ntplib  # pylint: disable=import-error
from time import ctime

# NTP_SERVER = 'ns1.luns.net.uk'
NTP_SERVER = 'uk.pool.ntp.org'


def getNtpTime():
    c = ntplib.NTPClient()
    try:
        response = c.request(NTP_SERVER, version=3)
        print('\n' + 30*'-')
        print('ntp time: ', ctime(response.tx_time))
        print(30*'-' + '\n')
    except:
        print('Could not get ntp time!')
