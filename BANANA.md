## Notes on getting the thing to work on something that isn't a Raspberry pi

In the code, see `# TODO BANANA: <a note>`

### Generally

- The lrpi_base image derives from `balenalib/raspberrypi3-debian:stretch` -> this probs isn't applicable anymore
- The arch may not be `armv7l`, on the Pine64 it's `aarch64` - what with the banana pi be?
- omxplayer hasn't had any updates in a while and is designed for the Rpi (3?) hardware. We might favour vlc going forward?
  - If we favour vlc (or something else) - the lrpi_base image needs to change
- If we don't ensure backwards compatibility with Rpi3, this becomes a hard fork
  - Although we can branch in the software if we maintain two testbeds
- NOTE that CD via Github and dockerhub means that if a new image is pushed to latest, all Pis will pull that image at 4am and potentially break the next day. We should be VVV CAREFUL here
