import appdaemon.appapi as appapi
import shelve
import time
import globals

#
# App to reset input_boolean, input_select, input_slider, device_tracker to previous values after HA restart
#
# Args:
#
#delay - amount of time after restart to set the switches
# 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class ControlBrightness(appapi.AppDaemon):

  def initialize(self):
    self.listen_state(self.state_change, "light", new="on")
       
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.now_is_between("sunset - 00:45:00", "22:00:00"):
      rBrightness = "200"
    elif self.now_is_between("22:00:00", "sunrise - 00:45:00"):
      rBrightness = "40"
    elif self.now_is_between("sunrise - 00:45:00", "sunset - 00:45:00"):
      rBrightness = "254"

    self.log("Setting brightness of " + str(entity) + " to " + str(rBrightness))
    self.turn_on(entity, brightness=rBrightness)
