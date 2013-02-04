// Firmware for controlling a Stepper Motor over USB, intended for use with ROS
// Floris van Breugel 2012

// Written for Arduino Uno


#include "Streaming.h"
#include "SerialReceiver.h"

SerialReceiver receiver;

// for UNO: 3, 5, 6, 9, 10, and 11. (the pins with the ~ next to them) 
// Provide 8-bit PWM output with the analogWrite() function
int clock_pin = 3;
int clock_interrupt = 1; // for Uno this interrupt corresponds to pin 3, and allows us to keep track of position
int dir_pin = 8;

// Variables, yes some of these could be ints instead of longs.
int absval;
bool interrupt_0 = 0;
bool interrupt_1 = 0;
bool interrupt_override = 1;
bool software_transmission = 0;
int interrupt_override_stepcounter = 0;
int interrupt_override_steptrigger = 0;
int dir = 0;
int action;
int value;
int pulse_counter = 0;
int interrupt_pin_0 = 0;
int interrupt_pin_1 = 1;
int increment_steps_delay = 5;

void setup()
{
  // start the serial for debugging
  Serial.begin(19200);
  
  // set direction pins to output, and initialize stepper motors to zero
  delay(1000);
  
  receiver.reset();
  
  pinMode(clock_pin,OUTPUT);
  pinMode(dir_pin,OUTPUT);
  
  interrupt_0 = 0;
  interrupt_1 = 0;
  interrupt_override = 1;
  software_transmission = 0;
  interrupt_override_stepcounter = 0;
  interrupt_override_steptrigger = 0;
  dir = 0;
  pulse_counter = 0;
  interrupt_pin_0 = 0;
  interrupt_pin_1 = 1;
  increment_steps_delay = 5;


  set_velocity_mode();
  
  // for UNO this allows pulse (step) counting on pin 3
  attachInterrupt(clock_interrupt, interrupt_handler, RISING);
  
  

}

void loop()
{  
  // read serial message, if available
  while (Serial.available() > 0) {
    receiver.process(Serial.read());
    if (receiver.messageReady()) {
        action = receiver.readInt(0);
        value = receiver.readInt(1);
        receiver.reset();
    }
  }
  
  check_interrupt_pins();
  if (interrupt_override==0) {
    handle_interrupt();
  }
  
  // check for interrupt timeout
  if ((interrupt_override==1) && (interrupt_override_steptrigger>0)) {
    if (abs(pulse_counter-interrupt_override_stepcounter) > interrupt_override_steptrigger) {
      interrupt_override = 0;
    }
  }


  if (action!=0) {
   performAction(action, value);
  } 
    
  // reset action
  action = 0;
}





///////////////////////////////////////////////////////////////////

void performAction(int action, int value) {
  switch (action) {
    // set velocity
    case 1: setVel_check_interrupt(value); break; 
    
    // disable interrupts
    case 2: interrupt_override = 1; interrupt_override_steptrigger = value; interrupt_override_stepcounter = pulse_counter; break;
    
    // get interrupt state
    case 3: Serial << interrupt_0 << "," << interrupt_1 << endl; break;
    
    // enable interrupts
    case 4: interrupt_override = 0; Serial << 1 << endl; break;
    
    // get position
    case 5: Serial << pulse_counter << endl; break;
    
    // set interrupt pins
    case 6: interrupt_pin_0 = value; Serial << 1 << endl; break;
    case 7: interrupt_pin_1 = value; Serial << 1 << endl; break;
    
    // reset step counter
    case 8: pulse_counter = 0; break;
    
    // increment steps (block or non blocking in python api)
    case 10: incrementSteps(value, 0); break;
    case 12: incrementSteps(value, 1); break;
    
    // set increment steps period
    case 11: increment_steps_delay = value; break;
    
    // set pwm frequency divisor
    case 101: setPwmFrequency(clock_pin, value); break;
    
    // set velocity mode
    case 102: set_velocity_mode(); break;
    
    // get interrupt override status
    case 1000: Serial << interrupt_override << endl; break;
  }
  
  
  
  
}


  
////////////////////////////////////////////////////////////////////
// increment steps
void incrementSteps(int value, int send_reply) {
  if (value<0) {
    dir = -1;
  }
  if (value>0) {
    dir = 1;
  }
  for (int i=0; i<abs(value); i++) {
    // check interrupt pins
    if (interrupt_override==0) {
      check_interrupt_pins();
      if ((interrupt_0==1) || (interrupt_1==1)) {
        if (send_reply==1) {
          Serial << pulse_counter << endl;
        }
        break;
      }
    }
    incrementStep(dir);
  }
  if (send_reply==1) {
    if ((interrupt_0==0) && (interrupt_1==0)) {
      Serial << pulse_counter << endl;
    }
  }
}

void incrementStep(int dir) {
  if (dir==1) {
    digitalWrite(dir_pin,HIGH);
  }
  if (dir==-1) {
    digitalWrite(dir_pin,LOW);
  }
  
  digitalWrite(clock_pin, HIGH);
  delayMicroseconds(increment_steps_delay);
  digitalWrite(clock_pin, LOW);
  delayMicroseconds(increment_steps_delay);
}

  
////////////////////////////////////////////////////////////////////
// set speed (if not interrupted, or if interrupted set speed to 0)
void handle_interrupt() {
  if ((interrupt_0==1) || (interrupt_1==1)) {
    setVel(0);
  }
}
  
void setVel_check_interrupt(int value) {
  if ( ((interrupt_0==0) && (interrupt_1==0)) || interrupt_override==1) {
    setVel(value);  
  }
}
  
void setVel(int value) {
    // set direction
    if (value > 0) {
      digitalWrite(dir_pin,HIGH);
      dir = 1;
    }
    if (value < 0) {
      digitalWrite(dir_pin,LOW);
      dir = -1;
    }
    
    // set speed
    // see python api for the heavy lifting
    absval = abs(value); // absolute value of speed
    int newVal = -1*(absval-256);
    if (newVal < 4) newVal = 4;
    OCR2A = newVal; 
}
  
  
  
/**
 * Divides a given PWM pin frequency by a divisor.
 *
 * The resulting frequency is equal to the base frequency divided by
 * the given divisor:
 *   - Base frequencies:
 *      o The base frequency for pins 3, 9, 10, and 11 is 31250 Hz.
 *      o The base frequency for pins 5 and 6 is 62500 Hz.
 *   - Divisors:
 *      o The divisors available on pins 5, 6, 9 and 10 are: 1, 8, 64,
 *        256, and 1024.
 *      o The divisors available on pins 3 and 11 are: 1, 8, 32, 64,
 *        128, 256, and 1024.
 *
 * PWM frequencies are tied together in pairs of pins. If one in a
 * pair is changed, the other is also changed to match:
 *   - Pins 5 and 6 are paired on timer0
 *   - Pins 9 and 10 are paired on timer1
 *   - Pins 3 and 11 are paired on timer2
 *
 * Note that this function will have side effects on anything else
 * that uses timers:
 *   - Changes on pins 3, 5, 6, or 11 may cause the delay() and
 *     millis() functions to stop working. Other timing-related
 *     functions may also be affected.
 *   - Changes on pins 9 or 10 will cause the Servo library to function
 *     incorrectly.
 *
 * Thanks to macegr of the Arduino forums for his documentation of the
 * PWM frequency divisors. His post can be viewed at:
 *   http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1235060559/0#4
 */
void setPwmFrequency(int pin, int divisor) {
  byte mode;
  if(pin == 5 || pin == 6 || pin == 9 || pin == 10) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 64: mode = 0x03; break;
      case 256: mode = 0x04; break;
      case 1024: mode = 0x05; break;
      default: return;
    }
    if(pin == 5 || pin == 6) {
      TCCR0B = TCCR0B & 0b11111000 | mode;
    } else {
      TCCR1B = TCCR1B & 0b11111000 | mode;
    }
  } else if(pin == 3 || pin == 11) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 32: mode = 0x03; break;
      case 64: mode = 0x04; break;
      case 128: mode = 0x05; break;
      case 256: mode = 0x06; break;
      case 1024: mode = 0x07; break;
      default: return;
    }
    TCCR2B = TCCR2B & 0b11111000 | mode;
  }
}
   
void set_velocity_mode() {
  TCCR2A = _BV(COM2A0) | _BV(COM2B1) | _BV(WGM20);
  TCCR2B = _BV(WGM22) | _BV(CS22);
  OCR2A = 256;
  OCR2B = 1;
  setPwmFrequency(clock_pin, 64);
}  

          
void interrupt_handler() {
  pulse_counter = pulse_counter + dir;
}
  
  
void check_interrupt_pins() {
  // read analog pins 0 and 1 to test for interrupt status
  if (1) {
    if (analogRead(interrupt_pin_0)<100) {
      interrupt_0 = 1;
    } else {
      interrupt_0 = 0;
    }
    
    if (analogRead(interrupt_pin_1)<100) {
      interrupt_1 = 1;
    } else {
      interrupt_1 = 0;
    }
  }
}
