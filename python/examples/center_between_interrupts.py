import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

def center_stepper_motor_between_two_limit_switches(sign=-1, vel=1000, port='/dev/ttyACM1', baudrate=57600, timeout=1):
    '''
    This function was designed to move a slider on a linear stage between two optical detectors.
    
    When an optical detector is triggered, the motor flips direction. If the wrong optical trigger is tripped, the motor stops. 
    
    sign -- flips which direction the system moves.
    ncycles -- number of complete HALF cycles to go through. For one full period, do 2 cycles.

    '''
    astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    astep.reset_step_counter()
    astep.set_interrupt_pins(0,1)
    astep.enable_interrupts()
    
    ncycles = 2
    cycles = 0
    prev_interrupt = None

    while cycles < ncycles:
        interrupt_0, interrupt_1 = astep.get_interrupt_states()
        if interrupt_0 == 1:
            if prev_interrupt == 1:
                cycles += 1
                stepper_pos_0 = astep.get_pos()
            astep.disable_interrupts(500)
            astep.set_vel(-1*sign*vel)
            prev_interrupt = 0
        elif interrupt_1 == 1:
            if prev_interrupt == 0:
                cycles += 1
                stepper_pos_1 = astep.get_pos()
            astep.disable_interrupts(500)
            astep.set_vel(sign*vel)
            prev_interrupt = 1
        elif astep.frequency == 0:
            astep.set_vel(sign*vel)
        time.sleep(.1)
    astep.set_vel(0)
    
    print stepper_pos_0, stepper_pos_1
    print astep.get_pos()
    
    if stepper_pos_0 > stepper_pos_1:
        desired_pos = stepper_pos_1 + int((stepper_pos_0-stepper_pos_1)/2.)
    else:
        desired_pos = stepper_pos_0 + int((stepper_pos_1-stepper_pos_0)/2.)
    
    print 'desired: ', desired_pos
    time.sleep(0.5)
    astep.go_to_pos(desired_pos, vel)
    print astep.get_pos()
    

if __name__ == '__main__':        
    center_stepper_motor_between_two_limit_switches(port='/dev/ttyACM0', baudrate=19200, timeout=1)
    
