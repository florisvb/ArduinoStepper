import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

def test_pwm_frequency(f, port='/dev/ttyACM0', baudrate=57600, timeout=1):
    astep = Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    astep.set_vel(0)
    astep.reset_step_counter()
    time_start = time.time()
    time_elapsed = time.time() - time_start
    astep.set_vel(f)
    while time_elapsed < 1.:
        time_elapsed = time.time() - time_start
    astep.set_vel(0)
    pos = astep.get_pos()
    measured_frequency = float(pos) / float(time_elapsed)
    return measured_frequency
    
if __name__ == '__main__':
    frequency = 100 # in steps per second
    test_pwm_frequency(frequency, port='/dev/ttyACM0', baudrate=57600, timeout=1)
