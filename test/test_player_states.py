# pytest
# test plan (this is an e2e test ofc)
#
# start Server with a local settings / usb file
# test get track list
# test load a track, play it
# assert based on response from /status
#
# test crossfade, etc
#
# generate a random interaction sequence
# last sequence is always 'stop' (i.e. pressing the 'back' button)
# make sure that the player doesn't error by the end of it
#
#
# extra unit test plan
# DMX interpolator
# get track list content JSON generation (with error modes)
# lighting
# events could be spit out through a dummy lighting driver / events go into a text file (parsed before assertion)
# events should be cross referenced with audio player timelines
##
