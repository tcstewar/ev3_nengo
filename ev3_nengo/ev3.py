class EV3Device(object):
    class_dir = None

    def __init__(self, port, ev3, msg_period=0.01):
        self.port = port
        self.ev3 = ev3
        self.msg_period = msg_period
        self.find_path()
        self.initialize()

    def initialize(self):
        pass


class Sensor(EV3Device):
    mode = None

    def find_path(self):
        class_path = '/sys/class/%s' % self.class_dir
        for path in self.ev3.dir(class_path).split():
            if path.startswith('sensor'):
                port = self.ev3.read('%s/%s/port_name' % (class_path, path))
                assert port.startswith('in')

                if int(port[2]) == self.port:
                    self.path = '%s/%s' % (class_path, path)
                    self.ev3.write('%s/mode' % self.path, self.mode)

class Motor(EV3Device):
    class_dir = None

    def find_path(self):
        class_path = '/sys/class/%s' % self.class_dir
        for path in self.ev3.dir(class_path).split():
            if path.startswith('motor'):
                port = self.ev3.read('%s/%s/port_name' % (class_path, path))
                assert port.startswith('out')

                if port[3] == self.port:
                    self.path = '%s/%s' % (class_path, path)

class IRProx(Sensor):
    class_dir = 'lego-sensor'
    mode = 'IR-PROX'

    def read(self):
        value = self.ev3.read('%s/value0' % self.path,
                              msg_period=self.msg_period)
        return float(value) / 100
    
class Ultrasonic(Sensor):
    class_dir = 'lego-sensor'
    mode = 'US-DIST-CM'

    def read(self):
        value = self.ev3.read('%s/value0' % self.path,
                              msg_period=self.msg_period)
        try:
            return float(value) / 255
        except:
            return 0

class TachoMotor(Motor):
    class_dir = 'tacho-motor'

    def initialize(self):
        self.ev3.write('%s/command' % self.path, 'run-direct')
        self.ev3.on_no_message(self.stop)

    def set_power(self, value):
        value = '%d' % max(min(int(value * 100), 100), -100)
        self.ev3.write('%s/duty_cycle_sp' % self.path, value,
                       msg_period=self.msg_period)

    def get_position(self):
        return self.ev3.read('%s/position' % self.path)

    def set_position(self, value):
        return self.ev3.write('%s/position' % self.path, '%d' % value)


    def stop(self):
        self.ev3.write('%s/duty_cycle_sp' % self.path, '0')

    
if __name__ == '__main__':
    import ev3_nengo.ev3link

    ev3 = ev3_nengo.ev3link.EV3Link('10.42.0.3')
    ev3.wait_for_connection()

    motor = TachoMotor('A', ev3, msg_period=0.1)
    irprox = IRProx(1, ev3, msg_period=0.1)
    us = Ultrasonic(3, ev3, msg_period=0.1)

    data = []
    t = []
    import time
    start = time.time()
    while time.time() - start < 3:
        motor.set_power((time.time()-start) % 1.0)
        data.append((irprox.read(), us.read()))
        t.append(time.time()-start)
        print data[-1]
    print 'elapsed', time.time()-start

    import pylab
    pylab.plot(t, data)
    pylab.show()
