import matplotlib.pyplot as plt
import time
import numpy as np
import arduino_stepper.arduino_stepper as arduino_stepper

    
if __name__ == '__main__':

    # set up variables for serial communication
    port = '/dev/ttyACM0'
    baudrate = 19200
    timeout = 1
    
    # instantiate stepper class
    print 'Initiating arduino, allow a few seconds'
    astep = arduino_stepper.Arduino_Stepper(port=port,timeout=timeout, baudrate=baudrate)
    print
    
    # reset position to zero
    astep.reset_step_counter()
    
    # go forward 500 steps at 200 Hz
    print 'Moving forward 500 steps at 200 Hz'
    astep.go_to_pos(500, 200, wait_until_done=True)
    
    # get position, and print it to the console - it had better be 500. Also, show roundtrip latency
    t = time.time()
    print 'Stepper Position: ', astep.get_pos()
    print 'Roundtrip Latency: ', time.time()-t, ' sec'
    print 
    
    # pause for 1 second
    print 'pausing'
    time.sleep(1)
    print
    
    # move at 500 Hz for 2 second. Then stop. Then move at 500 Hz in the opposite direction for 1 second.
    print 'Moving in square wave'
    t_start = time.time()
    t_elapsed = time.time()-t_start
    astep.set_vel(500)
    while t_elapsed < 2:
        t_elapsed = time.time()-t_start
    astep.set_vel(0)
    
    t_start = time.time()
    t_elapsed = time.time()-t_start
    astep.set_vel(-500)
    while t_elapsed < 2:
        t_elapsed = time.time()-t_start
    astep.set_vel(0)
    print
    
    # pause for 1 second
    print 'pausing'
    time.sleep(1)
    print
    
    # move at 440 Hz for 1 second, and print out the position every 0.05 seconds
    print 'Moving at 440 Hz and sending position data'
    t_start = time.time()
    t_prev = t_start
    t_elapsed = time.time()-t_start
    astep.set_vel(440)
    while t_elapsed < 1:
        t_now = time.time()
        t_elapsed = t_now-t_start
        if t_now-t_prev >= 0.05:
            print 'Stepper Position: ', astep.get_pos()
            t_prev = t_now
    astep.set_vel(0)
    print 
    
    print 'Done!'
