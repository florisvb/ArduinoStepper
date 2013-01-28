// Firmware for controlling a Stepper Motor over USB, intended for use with ROS
// Floris van Breugel 2012

// Written for Arduino Uno


#include "Streaming.h"
#include "SerialReceiver.h"

SerialReceiver receiver;

// for UNO: 3, 5, 6, 9, 10, and 11. (the pins with the ~ next to them) 
// Provide 8-bit PWM output with the analogWrite() function
int clock_pin= 3;
int dir_pin = 8;

// Variables used for decoding and delimiting TCP msg
long spd;
long absspd;
bool interrupt_0 = 0;
bool interrupt_1 = 0;
bool interrupt_override = 0;
long action;
long value;
long interrupt_override_timer = 0;
long interrupt_override_timeout = 0;


void setup()
{
  // start the serial for debugging
  Serial.begin(19200);
  
  // set direction pins to output, and initialize stepper motors to zero
  delay(1000);
  pinMode(clock_pin,OUTPUT);
  pinMode(dir_pin,OUTPUT);

  TCCR2A = _BV(COM2A0) | _BV(COM2B1) | _BV(WGM20);
  TCCR2B = _BV(WGM22) | _BV(CS22);
  OCR2A = 256;
  OCR2B = 1;
  setPwmFrequency(3, 1024);
  
  spd = 0;

}

void loop()
{
  if (analogRead(0)<100) {
    interrupt_0 = 1;
  } else {
    interrupt_0 = 0;
  }
  
  if (analogRead(1)<100) {
    interrupt_1 = 1;
  } else {
    interrupt_1 = 0;
  }
  
  if (interrupt_override==1) {
    if ((millis()-interrupt_override_timer) > interrupt_override_timeout) {
      interrupt_override = 0;
    }
  }
  
  while (Serial.available() > 0) {
    receiver.process(Serial.read());
    if (receiver.messageReady()) {
        action = receiver.readLong(0);
        value = receiver.readLong(1);
        receiver.reset();
        //Serial << interrupt_0 << ", " << interrupt_1 << ", " << (((interrupt_0==1) || (interrupt_1==1)) && interrupt_override==0) << "," << action << "," << value << endl;
    }
  }
        
  
    
  // set speed (if not interrupted)
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
    }
    if (spd < 0) {
      digitalWrite(dir_pin,LOW);
    }
    
    // software transmission to allow for wider speed range with smooth transition
    absspd = abs(spd); // absolute value of speed
    if (absspd <= 250) {
      setPwmFrequency(clock_pin, 1024);
      int newVal = -1*(absspd-256);
      if (newVal < 4) newVal = 4;
      OCR2A = newVal;
    }
    if (absspd > 250) {
      setPwmFrequency(clock_pin, 64);
      int newVal = -1*(absspd-256-256)-192+25;
      if (newVal < 20) newVal = 20;
      OCR2A = newVal;
    }
    
  }

  // interrupt_override
  if (action==2) {
    interrupt_override = 1;
    interrupt_override_timeout = value;
    interrupt_override_timer = millis();
  }
  
  // get interrupt state
  if (action==3) {
    delay(1);
    Serial << interrupt_0 << "," << interrupt_1 << endl;
  }
    
  
  action = 0;
        
    
  
  delay(1);
  
    
    
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
      case 1024: mode = 0x7; break;
      default: return;
    }
    TCCR2B = TCCR2B & 0b11111000 | mode;
  }
}
   
          
