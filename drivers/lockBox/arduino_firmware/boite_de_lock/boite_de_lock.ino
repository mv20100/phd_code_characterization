#define out 5
int ByteReceived;

void setup()
{
  Serial.begin(9600); 
  pinMode(out, OUTPUT);
}

void loop()
{
  if (Serial.available() > 0)
  {
    ByteReceived = Serial.read();
    
    if(ByteReceived == 'H')
    {
      digitalWrite(out,HIGH);
      Serial.println("Lock ON");
    }
    
    if(ByteReceived == 'L')
    {
      digitalWrite(out,LOW);
      Serial.println("Lock OFF");
    }
  
  }
}
