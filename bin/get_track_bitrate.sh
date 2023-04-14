mplayer -vo null -ao null -identify -frames 0 $1 | grep AUDIO_BITRATE

# with mpv
# mpv --script=/home/jib/workshop/mpv/stats.lua 02_Tales_of_bath_Poem.mp4

# where stats.lua is from:
# https://github.com/mpv-player/mpv/blob/master/player/lua/stats.lua