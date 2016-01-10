#!/usr/bin/python

import time
import os
import sys, traceback
import logging
import logging.handlers
import requests
import json

from ConfigParser import SafeConfigParser

###########################
# PERSONAL CONFIG FILE READ
###########################

parser = SafeConfigParser()
parser.read('wakeup.ini')

# Read path to log file
LOG_FILENAME = parser.get('config', 'log_filename')

# Read base url to use on Hue bridge
URL = parser.get('config', 'url')

# Read light hue param
LIGHT_HUE = parser.getint('config', 'light_hue')

# Read light saturation param
LIGHT_SAT = parser.getint('config', 'light_saturation')

# Read total light ramp-up time
TOTAL_RAMP_TIME = parser.getfloat('config', 'total_rampup_time')

# Read total light ramp-up time
NB_STEPS = parser.getint('config', 'nb_steps')

# Read total light ramp-up time
START_BRI = parser.getint('config', 'start_brightness')

# Read total light ramp-up time
END_BRI = parser.getint('config', 'end_brightness')

# Read total light ramp-up time
STAY_ON_TIME = parser.getfloat('config', 'stay_on_time')

#################
#  LOGGING SETUP
#################
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

def setLight(data):

    #logger.info("Sending to url" + URL)
    #logger.info("Sending data" + str(data))

    r = requests.put(URL, json.dumps(data), timeout=5)

    if r.status_code != 200:
        logger.info("Received response {c} from {u}".format(c=r.status_code, u=URL))

    resp = r.json()

    if type(resp)==list:
        successes = [m['success'] for m in resp if 'success' in m]
        errors = [m['error']['description'] for m in resp if 'error' in m]
        
        if errors:
            logger.info("FAILED:")
            logger.info("\n".join(errors))
        
        #if successes:
        #    logger.info("SUCCESSFUL: "+str(successes))     

#################
#  LIGHT RAMP-UP
#################
data_on = {"on":True}
data_on["sat"] = LIGHT_SAT
data_on["hue"] = LIGHT_HUE
data_on["bri"] = START_BRI

data_off = {"on":False}

logger.info('Starting light brightness ramp-up')

for i in range(NB_STEPS):
    data_on["bri"] = START_BRI + ((i+1)*(END_BRI-START_BRI)/NB_STEPS)
    setLight(data_on)
    time.sleep(TOTAL_RAMP_TIME/NB_STEPS)

logger.info('full brightness reached')

time.sleep(STAY_ON_TIME)

setLight(data_off)

logger.info('Light turned off, exiting')
