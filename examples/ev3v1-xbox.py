import ev3_nengo.ev3link
import nengo_xbox

if not hasattr(ev3_nengo, 'link'):
    ev3_nengo.link = ev3_nengo.ev3link.EV3Link('192.168.0.189')
link = ev3_nengo.link

print link.dir('/sys/class/tacho-motor')

import nengo
import numpy as np

import time

class EV3(nengo.Network):
    def __init__(self, label=None):
        super(EV3, self).__init__(label=label)
        self.last_times = {}
        
        with self:
            self.motor0 = nengo.Node(lambda t, x: self.motor(0, x), size_in=1)
            self.motor1 = nengo.Node(lambda t, x: self.motor(1, x), size_in=1)
            self.motor2 = nengo.Node(lambda t, x: self.motor(2, x), size_in=1)
        
        for i in [0, 1, 2]:
            link.write('/sys/class/tacho-motor/motor%d/run' % i, '1')
            link.write('/sys/class/tacho-motor/motor%d/run_mode' % i, 'forever')
            link.write('/sys/class/tacho-motor/motor%d/stop_mode' % i, 'coast')
            link.write('/sys/class/tacho-motor/motor%d/regulation_mode' % i, 'off')
            
        
    def motor(self, index, x):
        x = np.clip(int(x*100), -100, 100)
        link.write('/sys/class/tacho-motor/motor%d/duty_cycle_sp' % index, '%d'%x,
                       msg_period=0.1)



model = nengo.Network()
with model:
    ev3 = EV3()
    
    xbox = nengo_xbox.Xbox()
    nengo.Connection(xbox.axis[0], ev3.motor0)
    nengo.Connection(xbox.axis[1], ev3.motor1)
    nengo.Connection(xbox.axis[2], ev3.motor2)
    
    

