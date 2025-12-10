from test import ElmoEmotionManager
from ElmoV2API import ElmoV2API
import time

ROBOT_IP = "192.168.0.104"  # your Elmo IP

elmo = ElmoEmotionManager(ElmoV2API(ROBOT_IP))

try:
    '''
    while True:
    
        # Neutral at start
        elmo.set_emotion("neutral")
        time.sleep(10)
        # Later on, when something good happens:
        elmo.set_emotion("happy")
        time.sleep(10)

        # When robot expresses sadness:
        elmo.set_emotion("sad")
        time.sleep(10)

        # When it's tired:
        elmo.set_emotion("tired")
        time.sleep(10)

        # Keep your experiment loop running here...
    
    '''
    elmo.set_emotion("fear")

    while True:
        pass

except KeyboardInterrupt:
    elmo.stop()
