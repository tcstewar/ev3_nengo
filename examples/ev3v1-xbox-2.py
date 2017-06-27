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
            self.motors = nengo.Node(None, size_in=3)
            self.motor0 = nengo.Node(lambda t, x: self.motor(0, x), size_in=1)
            self.motor1 = nengo.Node(lambda t, x: self.motor(1, x), size_in=1)
            self.motor2 = nengo.Node(lambda t, x: self.motor(2, x), size_in=1)
            nengo.Connection(self.motors[0], self.motor0, synapse=None)
            nengo.Connection(self.motors[1], self.motor1, synapse=None)
            nengo.Connection(self.motors[2], self.motor2, synapse=None)
            
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
    
    xyr = nengo.Ensemble(n_neurons=300, dimensions=3, radius=1.7)
    
    nengo.Connection(xbox.axis[:3], xyr)
    
    transform = np.array([[0.5,1,-0.5], [-1,0,-1], [1,-1,-1]])
    
    nengo.Connection(xyr, ev3.motors, transform=transform.T)
    

def on_pause(sim):
    link.write('/sys/class/tacho-motor/motor0/duty_cycle_sp', '0')
    link.write('/sys/class/tacho-motor/motor1/duty_cycle_sp', '0')
    link.write('/sys/class/tacho-motor/motor2/duty_cycle_sp', '0')
    

