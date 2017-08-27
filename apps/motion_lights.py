import appdaemon.appapi as appapi
import datetime

##############################################################################################
# Args:
#
# sensor: Binary sensor to use as trigger. several motion detectors are separated with a comma.
# entity_on : Comma separated list of entities to turn on when detecting motion. Can be a light, script, scene or anything else that can be turned on.
# entity_off : Comma separated list of entities to turn off when detecting motion. Can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on. 
# delay: Amount of time after turning on to turn off again. If not specified defaults to 60 seconds.
# countdown: Sensor name for a countdown timer
#
# Release Notes
#
# Version 2:
#   Combined "best bits" from various versions (danielfaulknor)
#   Added countdown timer (with modifications) from aimc (danielfaulknor)
# Version 1.1:
#   Added option for several lights, scripts, scenes (Rene Tode)
#   Added option for several motiondetectors (Rene Tode)
#   Added option to just turn out light after timer ended (Rene Tode)
#   Added control if timer from motionsensor is longer then the delay (Rene Tode)
#   Changed handlenaming bug (Rene Tode)
#   Changed reset flow (Rene Tode)
# Version 1.0:
#   Initial Version (aimc)
##############################################################################################

class MotionLights(appapi.AppDaemon):

  def initialize(self):
    
    self.handle = None

    # Pull in sensors that will trigger the ON action
    if "sensor" in self.args:
      self.sensors = self.args["sensor"].split(",")
      for sensor in self.sensors:
        self.listen_state(self.motion, sensor)
    else:
      self.log("No sensor specified, doing nothing")

    # Add entities that we want to switch ON when the sensor goes ON
    if "entity_on" in self.args:
      on_entities = self.args["entity_on"].split(",")
      for on_entity in on_entities:
        # Watch for other things turning these OFF, so we can give up
        self.listen_state(self.off, on_entity)
    else:
      self.log("No entity to turn on specified")

    # Define delay for time to turn OFF after last time the sensor goes ON
    if "delay" in self.args:
      self.delay = self.args["delay"]
    else:
      self.delay = 60

    self.count = int(self.delay)
  
  # Callback function for something else turning one of our entities OFF    
  def off(self, entity, attribute, old, new, kwargs):
    if self.get_state(entity) == "off":
      self.log("reset handle, because {} was turned off".format(entity))
      self.cancel()
      self.handle = None

  # Callback function for when one of our sensors goes ON    
  def motion(self, entity, attribute, old, new, kwargs):
    # Check that sensor has changed from OFF to ON
    if new == "on":
      # If we don't already have a handle, it means this is the first time motion has occured
      if self.handle == None:
        if "entity_on" in self.args:
          on_entities = self.args["entity_on"].split(",")
          for on_entity in on_entities:
            # Turn 'em on
            self.turn_on(on_entity)
          self.log("First motion detected: i turned {} on, and set timer".format(self.args["entity_on"]))
        else:
          self.log("First motion detected: i turned nothing on, but did set timer")          
	# Start timer (and countdown clock)
        now = self.datetime()
        self.handle = self.run_every(self.light_check, now, 1)
      else:
        # We have a handle, so reset the timer
        self.cancel()
        now = self.datetime()
        self.handle = self.run_every(self.light_check, now, 1)
        self.log("Motion detected again, reset timer")
  
  # Callback on timer tick to update the countdown sensor and check if we're out of time
  def light_check(self, kwargs):
    self.count -= 1
    # Update countdown sensor
    self.set_countdown(str(datetime.timedelta(seconds=self.count)))
    # If we're at 0, turn our entities off
    if self.count <= 0:
      if "entity_off" in self.args:
          self.log("Turning {} off".format(self.args["entity_off"]))
          self.turn_off(self.args["entity_off"])
      self.cancel()

  # Function to cancel the timer if we're out of time or something else turned it off
  def cancel(self):
    self.log("Cancelling timer")
    self.count = int(self.delay)
    self.cancel_timer(self.handle)
    self.set_countdown("-")

  # Function to update the countdown timer if it is configured
  def set_countdown(self, value):
    if "countdown" in self.args:
      self.set_state(self.args["countdown"], state = value)
