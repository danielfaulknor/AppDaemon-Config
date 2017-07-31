
import appdaemon.appapi as appapi
import datetime

##############################################################################################
# Args:
#
# sensor: binary sensor to use as trigger. several motion detectors are seperated with ,
# entity_on : entity to turn on when detecting motion, can be a light, script, scene or anything else that can be turned on. more lights are sepetated with ,
# entity_off : entity to turn off when detecting motion, can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on. more lights are sepetated with ,
# delay: amount of time after turning on to turn off again. If not specified defaults to 60 seconds.
#
# Release Notes
#
# Version 1.1:
#   Added option for several lights, scripts, scenes (Rene Tode)
#   Added option for several motiondetectors (Rene Tode)
#   Added option to just turn out light after timer ended (Rene Tode)
#   Added controle if timer from motionsensor is longer then the delay (Rene Tode)
#   Changed handlenaming bug (Rene Tode)
#   Changed reset flow (Rene Tode)
# Version 1.0:
#   Initial Version (aimc)

class MotionLights(appapi.AppDaemon):

  def initialize(self):
    
    self.handle = None

    if "sensor" in self.args:
      self.sensors = self.args["sensor"].split(",")
      for sensor in self.sensors:
        self.listen_state(self.motion, sensor)
    else:
      self.log("No sensor specified, doing nothing")

    if "entity_on" in self.args:
      on_entities = self.args["entity_on"].split(",")
      for on_entity in on_entities:
        self.listen_state(self.off, on_entity)
    else:
      self.log("No entity to turn on specified")

    if "delay" in self.args:
      self.delay = self.args["delay"]
    else:
      self.delay = 60

    self.count = int(self.delay)
      
  def off(self, entity, attribute, old, new, kwargs):
    if self.get_state(entity) == "off":
      self.log("reset handle, because {} was turned off".format(entity))
      self.cancel()
      self.handle = None
    
  def motion(self, entity, attribute, old, new, kwargs):
    if "delay" in self.args:
      delay = self.args["delay"]
    else:
      delay = 60
      
    if new == "on":
      if self.handle == None:
        if "entity_on" in self.args:
          on_entities = self.args["entity_on"].split(",")
          for on_entity in on_entities:
            self.turn_on(on_entity)
          self.log("First motion detected: i turned {} on, and set timer".format(self.args["entity_on"]))
        else:
          self.log("First motion detected: i turned nothing on, but did set timer")          
        now = self.datetime()
        self.handle = self.run_every(self.light_check, now, 1)
      else:
        self.cancel()
        now = self.datetime()
        self.handle = self.run_every(self.light_check, now, 1)
        self.log("Motion detected again, reset timer")
  
  def light_check(self, kwargs):
    self.count -= 1
    self.log(self.count)
    self.set_countdown(str(datetime.timedelta(seconds=self.count)))
    if self.count <= 0:
      if "entity_off" in self.args:
          self.log("Turning {} off".format(self.args["entity_off"]))
          self.turn_off(self.args["entity_off"])
      self.cancel()

  def cancel(self):
    self.log("Cancelling timer")
    self.count = int(self.delay)
    self.cancel_timer(self.handle)
    self.set_countdown("-")

  def set_countdown(self, value):
    if "countdown" in self.args:
      self.set_state(self.args["countdown"], state = value)
