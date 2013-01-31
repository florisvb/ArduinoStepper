import serial
import time
import numpy as np

class Arduino_Stepper(serial.Serial):
    def __init__ (self, arduino_board='uno', clock_pin=3, **kwargs):
        super(Arduino_Stepper,self).__init__(**kwargs)
        time.sleep(2)
        
        if arduino_board=='uno' and clock_pin==3:
            self.divisors = {1: 31250, 8: 3906.25, 32: 976.5625, 64: 488.28125, 128: 244.140625, 256: 122.0703125, 1024: 30.517578125}
        else:
            raise ValueError('This function is currently only implemented for the Arduino Uno, on pin 3')
        
        self.pwm_frequency_divisor = 0
        self.pwm_speed = 0
        self.frequency = 0
        self.position = 0
        
        self.mode = 'velocity'
        
    def _set_pwm_speed(self, pwm_speed):
        self.write('[%s,%s]\n'%(1,pwm_speed))
        self.pwm_speed = pwm_speed
    
    def _set_pwm_frequency_divisor(self, val):
        # val: 1, 8, 32, 64, 128, 256, 1024
        if self.pwm_frequency_divisor != val:
            self.write('[%s,%s]\n'%(101,val))
            self.pwm_frequency_divisor = val
            
    def _set_velocity_mode(self):
        if self.mode != 'velocity':
            self.write('[%s,%s]\n'%(102,0))
            self.mode = 'velocity'
            
    def set_vel(self, frequency):
        '''
        Sets frequency to as close as possible to the desired frequency, using frequency divisors and pwm_speeds. Only updates arduino if the values are different than those that were commanded last time.
        
        frequency -- steps per second
        '''
        self._set_velocity_mode()
        
        if frequency == 0:
            self._set_pwm_speed(0)
            self.frequency = frequency
            return
        
        if np.abs(frequency) > np.min(self.divisors.values()):
            pwm_speed, divisor = self._get_pwm_speed_and_divisor(np.abs(frequency))
        else:
            pwm_speed = 0
            divisor = self.pwm_frequency_divisor
            
        if self.frequency != frequency:
            self._set_pwm_speed(pwm_speed*np.sign(frequency))
        if divisor != self.pwm_frequency_divisor:
            self._set_pwm_frequency_divisor(divisor)
            
        self.frequency = frequency
        
    def enable_interrupts(self):
        self.write('[%s,%s]\n'%(4,0))
        
    def disable_interrupts(self, steps=10):
        # disables all interrupts (set via set_interrupt_pins) for X number of steps
        self.write('[%s,%s]\n'%(2,steps))
        
    def set_interrupt_pins(self, pin0=0, pin1=1):
        # corresponds to analog input pins
        self.write('[%s,%s]\n'%(6,pin0))
        self.write('[%s,%s]\n'%(7,pin1))
        
    def get_interrupt_states(self):
        self.write('[%s,%s]\n'%(3,0))
        while 1:
            data = self.readline().strip()
            if data is not None and len(data) > 0:
                interrupt_0, interrupt_1 = data.split(',')
                interrupt_0 = int(interrupt_0)
                interrupt_1 = int(interrupt_1)
                
                return interrupt_0, interrupt_1
        
    def get_pos(self, timeout=10000):
        self.write('[%s,%s]\n'%(5,0))
        tstart = time.time()
        while time.time() - tstart < timeout:
            data = self.readline().strip()
            if data is not None and len(data) > 0:
                pos = int(data)
                self.position = pos
                return pos
        else:
            self.position = 0
            return 0
            
    def go_to_pos_vel_control(self, desired_position, maxvel=500, acceptable_error=1, gain_proportional=1, gain_integral=0.001, integral_memory=20):
        '''
        Uses a PI controller to drive the stepper motor to a desired position within an acceptable error and a maximum velocity.
        
        Returns the final position.
        
        This is a blocking function in python, but not on the arduino. 
        '''
        error = desired_position - self.get_pos()
        error_history = []
        current_position = self.get_pos()
        dt = 0.001
        while np.abs(error)>=acceptable_error:
            time_loop_start = time.time()
            current_position = self.get_pos()
            error = desired_position - self.get_pos()
            error_history.append(error)
            
            if len(error_history)>integral_memory:
                error_history.pop(0)
            
            integrated_error = np.sum(error_history)/dt
            vel = error*gain_proportional + integrated_error*gain_integral
            
            if vel>maxvel:
                vel = maxvel
            if vel<-1*maxvel:
                vel = -1*maxvel
            self.set_vel(vel)
            
            dt = time.time() - time_loop_start
            
        self.set_vel(0)
        return current_position
        
    def reset_step_counter(self):
        self.write('[%s,%s]\n'%(8,0))
        self.position = 0
                
    def _get_divisor_for_frequency(self, f):
        '''
        Returns the divisor that gives that highest resolution for the desired frequency.
        
        If there are none, it defaults to the lowest speed (highest resolution for zero vel
        '''
        divisors = self.divisors
        diff = f - np.array(divisors.values())
        pos_diff = np.where(diff>0)[0]
        try:
            key_index = pos_diff[np.argmin(diff[pos_diff])]
        except:
            key_index = np.argmin(divisors.values())
        
        return divisors.keys()[key_index]
        
    def _get_pwm_speed_for_frequency_and_divisor(self, f, d):
        divisors = self.divisors
        minfreq = divisors[d]
        pwm_speed = 256-2**(8-np.log(f/minfreq)/np.log(2))+1
        return pwm_speed
        
    def _get_pwm_speed_and_divisor(self, f):
        divisor = self._get_divisor_for_frequency(f)
        pwm_speed = self._get_pwm_speed_for_frequency_and_divisor(f, divisor)
        return int(pwm_speed), divisor
        
    def increment_steps(self, nsteps, period=None, wait_until_done=False):
        '''
        Simple function to increment n steps, in either direction. Period sets the period of the increments, in microseconds.
        
        This is a blocking function on the arduino, meaning it will be looping until it gets to the desired position and will not recieve serial communications in the mean time. You can decide whether or not the python function is blocking using the wait_until_done flag.
        '''
        self.mode = 'position'
        
        self._set_pwm_frequency_divisor(64) # that's the default, this way the timer will work as expected
        if period is not None:
            self._set_increment_steps_period(period)
            
        if not wait_until_done:
            self.write('[%s,%s]\n'%(10,nsteps))
            return self.get_pos()
        else:
            self.write('[%s,%s]\n'%(12,nsteps))
            while 1:
                data = self.readline().strip()
                if data is not None and len(data) > 0:
                    if int(data) == 1:
                        return self.get_pos()
                
        
    def _set_increment_steps_period(self, val):
        self.write('[%s,%s]\n'%(11,int(val/2.)))
        
    def go_to_pos(self, pos, frequency, wait_until_done=True):
        '''
        Uses self.increment_steps to move the stepper to the desired position at the desired frequency (units: seconds). 
        
        This is a blocking function on the arduino, but not in python. If you want to block until done, set wait_until_done to True.
        '''
        current_pos = self.get_pos()
        increment = pos - current_pos
        period = int( (1/float(frequency))*1e6 )
        pos = self.increment_steps(increment, period, wait_until_done)
        
        return pos
        
        
##############################################################################################
            
if __name__ == '__main__':
    astep = Arduino_Stepper(port='/dev/ttyACM0',timeout=1, baudrate=57600)
