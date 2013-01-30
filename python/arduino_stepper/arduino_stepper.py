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
        
    def _set_pwm_speed(self, pwm_speed):
        self.write('[%s,%s]\n'%(1,pwm_speed))
        self.pwm_speed = pwm_speed
    
    def _set_pwm_frequency_divisor(self, val):
        # val: 1, 8, 32, 64, 128, 256, 1024
        self.write('[%s,%s]\n'%(101,val))
        self.pwm_frequency_divisor = val
        
    def set_vel(self, frequency):
        '''
        Sets frequency to as close as possible to the desired frequency, using frequency divisors and pwm_speeds. Only updates arduino if the values are different than those that were commanded last time.
        
        frequency -- steps per second
        '''
        
        if frequency == 0:
            self._set_pwm_speed(0)
            self.frequency = frequency
            return
        
        if np.abs(frequency) > np.min(self.divisors.values()):
            pwm_speed, divisor = self._get_pwm_speed_and_divisor(np.abs(frequency))
        else:
            pwm_speed = 0
            divisor = self.pwm_frequency_divisor
            
        if pwm_speed != self.pwm_speed or divisor != self.pwm_frequency_divisor:
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
            if data is not None:
                interrupt_0, interrupt_1 = data.split(',')
                interrupt_0 = int(interrupt_0)
                interrupt_1 = int(interrupt_1)
                
                return interrupt_0, interrupt_1
        
    def get_pos(self):
        self.flush()
        self.write('[%s,%s]\n'%(5,0))
        tstart = time.time()
        timeout = 1
        while time.time() - tstart < timeout:
            data = self.readline().strip()
            if data is not None and len(data) > 0:
                pos = int(data)
                self.position = pos
                return pos
        else:
            self.position = 0
            return 0
            
    def go_to_pos(self, desired_position, maxvel=500, acceptable_error=2, gain_proportional=1, gain_integral=1):
        error = desired_position - self.get_pos()
        error_history = []
        current_position = self.get_pos()
        while np.abs(error)>acceptable_error:
            current_position = self.get_pos()
            error = desired_position - self.get_pos()
            error_history.append(error)
            
            if len(error_history)>20:
                error_history.pop(0)
            
            integrated_error = np.sum(error_history)
            vel = error*gain_proportional + integrated_error*gain_integral
            
            if vel>maxvel:
                vel = maxvel
            if vel<-1*maxvel:
                vel = -1*maxvel
            self.set_vel(vel)
            
            print desired_position, current_position, vel
            
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
    
##############################################################################################
            
if __name__ == '__main__':
    astep = Arduino_Stepper(port='/dev/ttyACM0',timeout=1, baudrate=57600)
