const int realy = 27;

void setup() {
  Serial.begin(115200);
  pinMode(realy, OUTPUT);
  digitalWrite(realy, HIGH);
  Serial.write("....");
}

void loop() {
  String command = Serial.readStringUntil('\n'); 
  if (command=="0"){
    digitalWrite(realy, HIGH);
  }
  else if (command=="1"){
    digitalWrite(realy, LOW);
  }

  
  delay(10);
}
