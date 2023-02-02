# this program controll a servo

#from PCA9685 import PCA9685
#import time
#
#pwm = PCA9685(0x40, debug=False)
#pwm.setPWMFreq(50)

#======================================================================
#Reading single character by forcing stdin to raw mode
import sys
import termios
import tty

def readchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if ch == '0x03':
        raise KeyboardInterrupt
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)  # 16=Up, 17=Down, 18=Right, 19=Left arrows

# End of single character reading
#======================================================================

Pos = 1500  
Step = 5

class ServoDriver():
    def __init__(self,_channel=0):
        self.channel = _channel
  

    def runServo(self,_Pos):
        pwm.setServoPulse(self.channel,_Pos)

print("this is a servo motor driver test code")

Servo = ServoDriver()
# main loop
try:
    while True:
        keyp = readkey()
        if keyp == 'w' or ord(keyp) == 16:
            Pos += 5
            if(Pos >= 2500): 
                Pos = 2500
            if(Pos <= 500):
                Pos = 500
            print ('Up', Pos)
        elif keyp == 'z' or ord(keyp) == 17:
            Pos -= 5
            if(Pos >= 2500): 
                Pos = 2500
            if(Pos <= 500):
                Pos = 500
            print ('Down', Pos)
        elif ord(keyp) == 3:
            break
        
        Servo.runServo(Pos)

except KeyboardInterrupt:
    print('error')
