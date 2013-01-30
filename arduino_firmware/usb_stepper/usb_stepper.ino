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
long spd;
long absspd;
bool interrupt_0 = 0;
bool interrupt_1 = 0;
bool interrupt_override = 1;
bool software_transmission = 0;
long interrupt_override_stepcounter = 0;
long interrupt_override_steptrigger = 0;
long dir = 0;
long action;
long value;
int value_as_int;
long pulse_counter = 0;
long interrupt_pin_0 = 0;
long interrupt_pin_1 = 1;

void setup()
{
  // start the serial for debugging
  Serial.begin(57600);
  
  // set direction pins to output, and initialize stepper motors to zero
  delay(1000);
  pinMode(clock_pin,OUTPUT);
  pinMode(dir_pin,OUTPUT);

  TCCR2A = _BV(COM2A0) | _BV(COM2B1) | _BV(WGM20);
  TCCR2B = _BV(WGM22) | _BV(CS22);
  OCR2A = 256;
  OCR2B = 1;
  setPwmFrequency(3, 64);
  
  spd = 0;
  
  // for UNO this allows pulse (step) counting on pin 3
  attachInterrupt(clock_interrupt, interrupt_handler, RISING);

}

void loop()
{  
  // read serial message, if available
  while (Serial.available() > 0) {
    receiver.process(Serial.read());
    if (receiver.messageReady()) {
        action = receiver.readLong(0);
        value = receiver.readLong(1);
        receiver.reset();
    }
  }
  
  // read analog pins 0 and 1 to test for interrupt status
  if (interrupt_override==0) {
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
  
  // check for interrupt timeout
  if ((interrupt_override==1) && (interrupt_override_steptrigger>0)) {
    if (abs(pulse_counter-interrupt_override_stepcounter) > interrupt_override_steptrigger) {
      interrupt_override = 0;
    }
  }

  // set speed (if not interrupted, or if interrupted set speed to 0)
  if ((action==1) || ((interrupt_0==1) || (interrupt_1==1)) ) {
    //Serial << value << ", " << interrupt_0 << ", " << interrupt_1 << ", " << interrupt_override << endl;
    if ( ((interrupt_0==0) && (interrupt_1==0)) || interrupt_override==1) {
      if (action==1) {
        spd = value;
      }
    } else {
      spd = 0;
    }
    
    
    // set direction
    if (spd > 0) {
      digitalWrite(dir_pin,HIGH);
      dir = 1;
    }
    if (spd < 0) {
      digitalWrite(dir_pin,LOW);
      dir = -1;
    }
    
    // see python api for the heavy lifting
    absspd = abs(spd); // absolute value of speed
    int newVal = -1*(absspd-256);
    if (newVal < 4) newVal = 4;
    OCR2A = newVal;
     
  }

  // enable interrupt_override
  if (action==2) {
    interrupt_override = 1;
    interrupt_override_steptrigger = value;
    interrupt_override_stepcounter = pulse_counter;
  }
  
  // get interrupt state
  if (action==3) {
    Serial << interrupt_0 << "," << interrupt_1 << endl;
  }
  
  // disable interrupt override
  if (action==4) {
    interrupt_override = 0;
  }
  
  // get position
  if (action==5) {
    Serial << pulse_counter << endl;
  }
  
  // reset step counter
  if (action==8) {
    pulse_counter = 0;
  }
  
  // set interrupt pins
  if (action==6) {
    interrupt_pin_0 = value;
  }
  if (action==7) {
    interrupt_pin_1 = value;
  }
  
  // set speed range
  if (action==101) {
    value_as_int = (int) value;
    setPwmFrequency(clock_pin, value_as_int);
  }
    
  // reset action
  action = 0;

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
   
          
          
void interrupt_handler() {
  pulse_counter = pulse_counter + dir;
}
  
