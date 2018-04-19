OUT=0
IN=1
HIGH=1
LOW=0
PUD_DOWN=0
BOTH=2
BCM=0

def setmode(mode):
    pass

def setwarnings(value):
    pass

def setup(pin,value,pull_up_down=PUD_DOWN):
    pass

def output(pin,value):
    pass

def input(pin):
    return 0

def add_event_detect(pin, direction, callback, bouncetime=200):
    pass

def remove_event_detect(pin):
    pass