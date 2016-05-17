#include <SoftwareSerial.h>
#include <SerialCommand.h>
SerialCommand SCmd;   // The demo SerialCommand object

int power = 255;
int stbPow = 255;
int stepIndex = 0;
int counter = 0;
unsigned long currentMillis;
long previousMillis = 0; 
long interval = 4;
int stepsTodo = 0;
int dir = 0;
bool freeRun = false;

void setup() {
  
  //establish motor direction toggle pins
  pinMode(12, OUTPUT); //CH A -- HIGH = forwards and LOW = backwards???
  pinMode(13, OUTPUT); //CH B -- HIGH = forwards and LOW = backwards???
  
  //establish motor brake pins
  pinMode(9, OUTPUT); //brake (disable) CH A
  pinMode(8, OUTPUT); //brake (disable) CH B
  Serial.begin(19200);

  SCmd.addCommand("L",freeRunL);
  SCmd.addCommand("R",freeRunR);
  SCmd.addCommand("+",oneStepL);
  SCmd.addCommand("-",oneStepR);
  SCmd.addCommand("S",stopFreeRun);
  SCmd.addCommand("P?",getPosition);
  SCmd.addDefaultHandler(unrecognized);

}

void moveOneStep(){
    if(dir>0){
      counter = counter +1;
      stepIndex=(stepIndex+1)%4;
    }
    else{
      counter = counter -1;
      stepIndex=(stepIndex+3)%4;
    }
    switch (stepIndex) {
      case 0:
        digitalWrite(9, LOW);  //ENABLE CH A
        digitalWrite(8, HIGH); //DISABLE CH B
        digitalWrite(12, HIGH);   //Sets direction of CH A
        analogWrite(3, power);   //Moves CH A
        //Serial.println(String("Pos A (|) :"+String(counter)));
        break;
      case 1:
        digitalWrite(9, HIGH);  //DISABLE CH A
        digitalWrite(8, LOW); //ENABLE CH B
        digitalWrite(13, LOW);   //Sets direction of CH B
        analogWrite(11, power);   //Moves CH B
        //Serial.println(String("Pos B (/) :"+String(counter)));
        break;
      case 2:        
        digitalWrite(9, LOW);  //ENABLE CH A
        digitalWrite(8, HIGH); //DISABLE CH B
        digitalWrite(12, LOW);   //Sets direction of CH A
        analogWrite(3, power);   //Moves CH A
        //Serial.println(String("Pos C (-) :"+String(counter)));
        break;
      case 3:        
        digitalWrite(9, HIGH);  //DISABLE CH A
        digitalWrite(8, LOW); //ENABLE CH B
        digitalWrite(13, HIGH);   //Sets direction of CH B
        analogWrite(11, power);   //Moves CH B 
        //Serial.println(String("Pos D (\\) :"+String(counter)));
        break;
     }
     if(stepsTodo>0) stepsTodo = stepsTodo -1;
}

void standby(){
     analogWrite(11, stbPow);   //Moves CH B
     analogWrite(3, stbPow);   //Moves CH A
}

void moveNsteps(int n,int delayTime){
  for (int i=0; i < n; i++){
   moveOneStep();
   delay(delayTime);
  }
  standby();
}

void freeRunL(){
  freeRun = true ; 
  dir = 0 ;
}

void freeRunR(){
  freeRun = true ; 
  dir = 1 ;
}

void oneStepL(){
  freeRun = false ;
  dir = 0 ;
  stepsTodo = 1;
}

void oneStepR(){
  freeRun = false ;
  dir = 1 ;
  stepsTodo = 1;
}

void stopFreeRun(){
  freeRun = false ;
}

void getPosition(){
  Serial.println(counter);
}

void unrecognized(){
  Serial.println("What?"); 
}

void loop(){
  SCmd.readSerial();
  currentMillis = millis();
  if(currentMillis - previousMillis > interval) {
    // save the last time you blinked the LED 
    previousMillis = currentMillis;
    if(stepsTodo>0 || freeRun){
      moveOneStep();
    }
  }
}

