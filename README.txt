Version 0.0.1

The arduino firmware was written for and tested with an arduino UNO. 

Things to be aware of:

1. With software_transmission disabled (default) the speed is set with 8 bits, between 0 and 256. The actual speed of the motor depends on two things: (1) the setting on the motor; (2) the clock speed of the chip. The software_transmission enabled (via set_software_transmission(1)), the speed range is between 0 and 512. This could be expanded yet further. Note that this can affect functions that rely on millis().

Things that should be added asap: 

1. Currently there is no proper calibration between speed and steps per second
2. Step counting is not currently implemented
