import ev3_nengo.ev3link

if not hasattr(ev3_nengo, 'link'):
    ev3_nengo.link = ev3_nengo.ev3link.EV3Link('192.168.0.103')
link = ev3_nengo.link

print(link.dir('/sys/class/tacho-motor'))
print(link.dir('/sys/class/lego-sensor'))

import nengo
import numpy as np

import time

class EV3(nengo.Network):
    def __init__(self, label=None):
        super(EV3, self).__init__(label=label)

        with self:
            self.motor0 = nengo.Node(lambda t, x: self.motor(0, x), size_in=1)
            self.motor1 = nengo.Node(lambda t, x: self.motor(1, x), size_in=1)
            self.motor2 = nengo.Node(lambda t, x: self.motor(2, x), size_in=1)
            self.motors = nengo.Node(None, size_in=3)
            nengo.Connection(self.motors[0], self.motor0, synapse=None)
            nengo.Connection(self.motors[1], self.motor1, synapse=None)
            nengo.Connection(self.motors[2], self.motor2, synapse=None)

        
        for i in [0, 1, 2]:
            link.write('/sys/class/tacho-motor/motor%d/command' % i, 'run-direct')
        
        with self:
            self.vision = nengo.Node(lambda t: self.ir_sensor(0), size_out=1)
        link.write('/sys/class/lego-sensor/sensor0/mode', 'IR-PROX')
        
        self.last_ir = [0]
        
    def ir_sensor(self, index):
        v = link.read('/sys/class/lego-sensor/sensor0/value0', msg_period=0.1)
        if v is not None:
            try:
                self.last_ir[index] = float(v)/100
            except:
                pass
        return self.last_ir[index]


    def motor(self, index, x):
        x = np.clip(int(x*100), -100, 100)
        link.write('/sys/class/tacho-motor/motor%d/duty_cycle_sp' % index, '%d'%x,
                       msg_period=0.1)


def on_pause(sim):
    link.write('/sys/class/tacho-motor/motor0/duty_cycle_sp', '0')
    link.write('/sys/class/tacho-motor/motor1/duty_cycle_sp', '0')
    link.write('/sys/class/tacho-motor/motor2/duty_cycle_sp', '0')


def control(x):
    distance = x[0]
    
    if distance < 0.5:
        return 0, 0, 0
    else:
        return -1, 1, 1
    

model = nengo.Network()
with model:
    pass
    ev3 = EV3()
    
    
    nengo.Connection(ev3.vision, ev3.motors, function=control)
    
    ctrl = nengo.Node([0,0,0])
    nengo.Connection(ctrl[0], ev3.motor0)
    nengo.Connection(ctrl[1], ev3.motor1)
    nengo.Connection(ctrl[2], ev3.motor2)
    
