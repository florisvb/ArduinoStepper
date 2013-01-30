import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

def sin_curve_in_position(amplitude, frequency, time_to_wiggle_for=5, port='/dev/ttyACM0', baudrate=57600, timeout=1):
    '''
    
    '''
    def sinfunc(t):
        return amplitude*np.sin( t*2*np.pi*frequency )
    
    astep = Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    
    time_start = time.time()
    t = time.time() - time_start
    
    desired_position_array = []
    desired_position_time = []
    actual_position_array = []
    actual_position_time = []
    
    while t < time_to_wiggle_for:
        t = time.time() - time_start
        desired_position = sinfunc(t)
        desired_position_array.append(desired_position)
        desired_position_time.append(t)
        pos = astep.go_to_pos(desired_position, maxvel=5000, acceptable_error=1, gain_proportional=100, gain_integral=1)
        actual_position_array.append(pos)
        actual_position_time.append(time.time()-time_start)
        
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ax.plot(desired_position_time, desired_position_array, 'black')
    ax.plot(actual_position_time, actual_position_array, 'red')
        
    ax.set_xlabel('time, sec')
    ax.set_ylabel('value')
    
    
if __name__ == '__main__':
    amplitude = 100 # in steps
    frequency = 0.1 # in steps per second
    sin_curve_in_position(amplitude, frequency, time_to_wiggle_for=5, port='/dev/ttyACM0', baudrate=57600, timeout=1)
