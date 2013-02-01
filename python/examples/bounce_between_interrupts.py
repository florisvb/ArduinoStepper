import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

def example_drive_stepper_to_bounce_between_two_limit_switches(sign=-1, ncycles=2, vel=1000, port='/dev/ttyACM1', baudrate=19200, timeout=1):
    '''
    This function was designed to move a slider on a linear stage between two limit switches. Each limit switch as a direction of motion it triggers, so if the sign is correct the slider will bounce between the two positions, if the sign is wrong (backwards), the slider will crash. 
    
    sign -- flips which direction the system moves.
    ncycles -- number of complete HALF cycles to go through. For one full period, do 2 cycles.

    '''
    astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    
    astep.set_interrupt_pins(0,1)
    astep.enable_interrupts()
    
    cycles = 0
    prev_interrupt = None
    
    while cycles < ncycles:
        interrupt_0, interrupt_1 = astep.get_interrupt_states()
        if interrupt_0 == 1:
            astep.disable_interrupts(100)
            astep.set_vel(-1*sign*vel)
            if prev_interrupt == 1:
                cycles += 1
            prev_interrupt = 0
        elif interrupt_1 == 1:
            astep.disable_interrupts(100)
            astep.set_vel(sign*vel)
            if prev_interrupt == 0:
                cycles += 1
            prev_interrupt = 1
        elif astep.frequency == 0:
            astep.set_vel(vel)
    astep.set_vel(0)

if __name__ == '__main__':        
    example_drive_stepper_to_bounce_between_two_limit_switches(port='/dev/ttyACM0', baudrate=19200, timeout=1)
    
