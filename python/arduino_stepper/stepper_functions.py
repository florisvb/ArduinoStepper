import time
import numpy as np
import arduino_stepper

def bounce_between_two_limit_switches(sign=-1, ncycles=2, vel=1000, port='/dev/ttyACM1', baudrate=19200, timeout=1, astep=None):
    '''
    This function was designed to move a slider on a linear stage between two limit switches. Each limit switch as a direction of motion it triggers, so if the sign is correct the slider will bounce between the two positions, if the sign is wrong (backwards), the slider will crash. 
    
    sign -- flips which direction the system moves.
    ncycles -- number of complete HALF cycles to go through. For one full period, do 2 cycles.
    
    astep -- instance of Arduino_Stepper class, if None the function will create it's own instance using the given port and baudrate 

    '''
    
    if astep is None:
        
        print 'connecting to stepper'    
        is_connected = False
        n = 0
        while not is_connected:
            n += 1
            print 'nth try: ', n
            astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
            is_connected = astep.is_connected            

    print 'stepper connected'
        
    print astep.get_pos()
        
    print 'setting interrupt pins'
    astep.set_interrupt_pins(0,1)
    print 'enabling interrupts'
    astep.enable_interrupts()
    
    cycles = 0
    prev_interrupt = None
    
    print 'starting cycles'
    started = False
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
        elif not started:
            astep.set_vel(vel)
        started = True
    astep.set_vel(0)
    #astep.close()
    
    return 
