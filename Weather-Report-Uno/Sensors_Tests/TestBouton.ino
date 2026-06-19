#define BUTTON_PIN 7

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("[BUTTON] Initialisé sur la broche 7");
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("[BUTTON] Appui détecté! ");
    delay(500);  // Anti-rebond simple
    
    // Attendre le relâchement
    while (digitalRead(BUTTON_PIN) == LOW) {
      delay(10);
    }
    delay(200);  // Anti-rebond après relâchement
  }
}