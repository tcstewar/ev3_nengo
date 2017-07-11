import ev3_nengo.ev3link
import nstbot

if not hasattr(ev3_nengo, 'link'):
    ev3_nengo.link = ev3_nengo.ev3link.EV3Link('192.168.0.103')
if not hasattr(nstbot, 'bot'):
    bot = nstbot.RetinaBot()
    bot.connect(nstbot.Serial('COM7', baud=4000000))
    nstbot.bot = bot
link = ev3_nengo.link
bot = nstbot.bot
#bot.retina(True)
#bot.optic_flow()
bot.activate_sensors(gyro=True, accel=True, period=0.01)

import nengo
import numpy as np

import time

class EV3(nengo.Network):
    def __init__(self, label=None):
        super(EV3, self).__init__(label=label)
        self.last_times = {}
        
        with self:
            self.motor = nengo.Node(lambda t, x: self.motor_func(0, x), size_in=1)
            self.accel = nengo.Node(lambda t: bot.get_sensor('accel'))
            self.gyro = nengo.Node(lambda t: np.array(bot.get_sensor('gyro'))*10)
        
        
        for i in [0]:
            link.write('/sys/class/tacho-motor/motor%d/command' % i, 'run-direct')
            #link.write('/sys/class/tacho-motor/motor%d/run' % i, '1')
            #link.write('/sys/class/tacho-motor/motor%d/run_mode' % i, 'forever')
            #link.write('/sys/class/tacho-motor/motor%d/stop_mode' % i, 'coast')
            #link.write('/sys/class/tacho-motor/motor%d/regulation_mode' % i, 'off')
            
        
    def motor_func(self, index, x):
            x = np.clip(int(x*100), -100, 100)
            link.write('/sys/class/tacho-motor/motor%d/duty_cycle_sp' % index, '%d'%x,
                           msg_period=0.01 )


def get_flow(t):
    scale = 100
    return 0, 0
    #return nstbot.bot.vx*scale, nstbot.bot.vy*scale


model = nengo.Network()
with model:
    ev3 = EV3()
    
    ctrl = nengo.Node([0]) 
    nengo.Connection(ctrl, ev3.motor)
    
    flow = nengo.Node(get_flow)
    
    #nengo.Connection(flow[1], ev3.motor, transform=-1)
    
    gain = 2.0
    
    Kp = 5.0*gain
    Kd = 15.0*gain
    nengo.Connection(ev3.accel[0], ev3.motor, transform=Kp, synapse=None)
    nengo.Connection(ev3.gyro[2], ev3.motor, transform=-Kd, synapse=None)
    
    Ki = 0.5*gain
    
    int_ens = nengo.Ensemble(100, 1, neuron_type=nengo.LIFRate())
    nengo.Connection(int_ens, int_ens, synapse=0.1)
    nengo.Connection(ev3.accel[0], int_ens, synapse=None)
    nengo.Connection(int_ens, ev3.motor, transform=Ki, synapse=None)

    
    
    
    
def on_pause(sim):
    for index in [0]:
        link.write('/sys/class/tacho-motor/motor%d/duty_cycle_sp' % index, '0')
