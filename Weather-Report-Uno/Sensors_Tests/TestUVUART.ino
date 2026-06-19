#include "DFRobot_UVIndex240370Sensor.h"

// Arduino Renesas UNO utilise Serial1 par défaut
DFRobot_UVIndex240370Sensor UVIndex240370Sensor(&Serial1);

void setup() {
  Serial.begin(9600);   // Moniteur série
  Serial1.begin(9600);  // Communication avec le capteur
  delay(1000);
  
  while(UVIndex240370Sensor.begin() != true) {
    Serial.println("Sensor initialize failed!!");
    delay(2000);
  }
  Serial.println("Sensor initialize success!!");
}

void loop() {
  uint16_t voltage = UVIndex240370Sensor.readUvOriginalData();
  uint16_t index = UVIndex240370Sensor.readUvIndexData();
  uint16_t level = UVIndex240370Sensor.readRiskLevelData();
  
  Serial.print("voltage: "); Serial.print(voltage); Serial.println(" mV");
  Serial.print("index: "); Serial.println(index);
  
  if(level==0) Serial.println("Low Risk");
  else if(level==1) Serial.println("Moderate Risk");
  else if(level==2) Serial.println("High Risk");
  else if(level==3) Serial.println("Very High Risk");
  else if(level==4) Serial.println("Extreme Risk");
  
  delay(1000);
}