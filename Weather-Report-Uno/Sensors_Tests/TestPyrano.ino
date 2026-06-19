#define PYRANO_PIN A1 // Modifier le numéro de pin selon la configuration
#define PYRANO_CALIBRATION 0.4  // W/m² per mV (serial > 10517) fournie par le fabricant pour SP215

void setup() {
  Serial.begin(9600);
  delay(1000);
  Serial.println("=== Pyranometer SP215 Test ===\n");
}

void loop() {
  // Lecture brute
  int rawValue = analogRead(PYRANO_PIN); // Lecture de la tension brute (0 = 0V et 1023 = 5V)
  
  // Conversion en mV (0-5V = 0-5000mV)
  float voltage_mV = (rawValue / 1023.0) * 5000.0;
  
  // Conversion en W/m²
  float radiation_Wm2 = voltage_mV * PYRANO_CALIBRATION;
  
  // Affichage
  Serial.print("Raw: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage_mV, 2);
  Serial.print(" mV | Radiation: ");
  Serial.print(radiation_Wm2, 1);
  Serial.println(" W/m2");
  
  delay(500);
}