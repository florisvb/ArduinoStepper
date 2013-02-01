import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

def sin_curve_in_position_with_vel_control(amplitude, frequency, time_to_wiggle_for=5, maxvel=5000, acceptable_error=2, gain_proportional=1, gain_integral=.001, port='/dev/ttyACM0', baudrate=19200, timeout=1):
    '''
    This does not reall work well.
    '''
    def sinfunc(t):
        return amplitude*np.sin( t*2*np.pi*frequency )
    
    astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    astep.reset_step_counter()

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
        pos = astep.go_to_pos_vel_control(desired_position, maxvel=5000, acceptable_error=2, gain_proportional=10, gain_integral=1)
        actual_position_array.append(pos)
        actual_position_time.append(time.time()-time_start)
        
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ax.plot(desired_position_time, desired_position_array, 'black')
    ax.plot(actual_position_time, actual_position_array, 'red')
        
    ax.set_xlabel('time, sec')
    ax.set_ylabel('value')
    
    
def sin_curve_in_position_with_pos_control(amplitude, frequency, time_to_wiggle_for=5, maxvel=5000, port='/dev/ttyACM0', baudrate=19200, timeout=1):
    '''
    
    '''
    def sinfunc(t):
        return amplitude*np.sin( t*2*np.pi*frequency )
    
    astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    astep.reset_step_counter()

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
        pos = astep.go_to_pos(desired_position, maxvel)
        actual_position_array.append(pos)
        actual_position_time.append(time.time()-time_start)
        
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ax.plot(desired_position_time, desired_position_array, 'black')
    ax.plot(actual_position_time, actual_position_array, 'red')
        
    ax.set_xlabel('time, sec')
    ax.set_ylabel('value')
    
    
if __name__ == '__main__':
    amplitude = 1000 # in steps
    frequency = 1 # in steps per second
    sin_curve_in_position_with_vel_control(amplitude, frequency, time_to_wiggle_for=10, port='/dev/ttyACM1', baudrate=19200, timeout=1)
