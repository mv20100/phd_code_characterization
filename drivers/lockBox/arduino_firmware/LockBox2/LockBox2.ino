#include <SoftwareSerial.h>
#include <SerialCommand.h>

#define out 5

SerialCommand SCmd;   // The demo SerialCommand object
int lock_state = 0;

void setup()
{  
  pinMode(out,OUTPUT);      // Configure the onboard LED for output
  Serial.begin(9600); 

  // Setup callbacks for SerialCommand commands 
  SCmd.addCommand("ON",lock_on);       // Turns LED on
  SCmd.addCommand("OFF",lock_off);        // Turns LED off
  SCmd.addCommand("LOCK?",getLockState);     // Echos the string argument back
  SCmd.addDefaultHandler(unrecognized);  // Handler for command that isn't matched  (says "What?") 
//  Serial.println("Ready"); 

}

void loop()
{  
  SCmd.readSerial();     // We don't do much, just process serial commands
}


void lock_on()
{
  digitalWrite(out,HIGH);
  lock_state = 1;
//  Serial.println("Lock ON");
}

void lock_off()
{
  digitalWrite(out,LOW);
  lock_state = 0;
//  Serial.println("Lock OFF");
}

void getLockState()
{
  Serial.println(lock_state); 
}

// This gets set as the default handler, and gets called when no other command matches. 
void unrecognized()
{
  Serial.println("What?"); 
}

