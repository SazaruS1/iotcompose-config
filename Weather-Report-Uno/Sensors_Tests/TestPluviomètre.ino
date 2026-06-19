#define RAIN_GAUGE_PIN 8  // Pin D8 

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  Serial.println("\n=== Test sur le pin D8 ===\n");
  
  pinMode(RAIN_GAUGE_PIN, INPUT_PULLUP);
}

int last_state = HIGH;

void loop() {
  int current_state = digitalRead(RAIN_GAUGE_PIN);
  
  if (current_state != last_state) {
    Serial.print("CHANGEMENT D'ETAT: ");
    Serial.print(last_state == HIGH ? "Haut" : "Bas");
    Serial.print(" → ");
    Serial.println(current_state == HIGH ? "Haut" : "Bas");
    last_state = current_state;
  }
  
  static unsigned long last_report = 0;
  if (millis() - last_report >= 3000) {
    last_report = millis();
    Serial.print("Pin D8: ");
    Serial.println(current_state == HIGH ? "Haut (5V)" : "Bas (0V)");
  }
  
  delay(50);
}