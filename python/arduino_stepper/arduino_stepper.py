import serial

class Arduino_Data_Transmission(serial.Serial):
    def __init__ (self, **kwargs):
        super(Arduino_Data_Transmission,self).__init__(**kwargs)
        
    def set_vel(self, vel):
        self.write('[%s,%s]\n'%(1,vel))
        
    def set_interrupt_override(self, timeout=10):
        self.write('[%s,%s]\n'%(2,timeout))
        
    def get_interrupt_state(self):
        self.write('[%s,%s]\n'%(3,0))
        
        while 1:
            data = self.readline().strip()
            
            if data is not None:
                print data
                interrupt_0, interrupt_1 = data.split(',')
                interrupt_0 = int(interrupt_0)
                interrupt_1 = int(interrupt_1)
                
                return interrupt_0, interrupt_1
                
    def set_software_transmission(self, bool_val):
        self.write('[%s,%s]\n'%(100,bool_val))
                
                
def example_drive_stepper_to_bounce_between_two_limit_switches():
    arduino_data_transmission = Arduino_Data_Transmission(port='/dev/ttyACM0',timeout=1, baudrate=19200)
    
    arduino_data_transmission.set_vel(300)
    while 1:
        interrupt_0, interrupt_1 = arduino_data_transmission.get_interrupt_state()
        if interrupt_0 == 1:
            arduino_data_transmission.set_interrupt_override(200)
            arduino_data_transmission.set_vel(-300)
        if interrupt_1 == 1:
            arduino_data_transmission.set_interrupt_override(200)
            arduino_data_transmission.set_vel(300)
        
    
    

if __name__ == '__main__':
    arduino_data_transmission = Arduino_Data_Transmission(port='/dev/ttyACM0',timeout=1, baudrate=19200)
