// Programme de réception de données provenant d'une API Météo et de lecture de capteurs (MS5637, UV Index, Pyranometre et Pluviometre)
// Une fois les données collectées, celles-ci vont êtres encodées en hexadécimal et transmises via un module LoRa Wio-E5 toutes les 13 minutes (ou en cas d'appui sur le bouton d'urgence)
// Les données encodées vont êtres collectées et décodées par Chirpstack
// Version pour la véritable API du Datalogger

#include <SPI.h>
#include <Arduino.h>
#include <Ethernet.h>
#include <BaroSensor.h>
#include "DFRobot_UVIndex240370Sensor.h"
#include <Wire.h>
#include <SoftwareSerial.h>


#define ENABLE_DIAGNOSTICS 1
#define VERBOSE_MODE 1
#define PYRANO_PIN A0
// #define PYRANO_PIN_2 A1
#define PYRANO_CALIBRATION 0.4
#define RAIN_GAUGE_PIN 8        
#define RAIN_PER_PULSE 0.2
#define DEBOUNCE_TIME 50

// ===== BUTTON CONFIG =====
#define BUTTON_PIN 7
#define BUTTON_COOLDOWN 10000  // 10 secondes entre 2 appuis

// ===== Codes d'alerte =====
#define ALERT_BATTERY_LOW 0xFF01  // Code d'alerte batterie faible

// ===== Commandes Progmem permettant de gagner de la RAM =====
const char PROGMEM STR_AT[] = "AT\r\n";
const char PROGMEM STR_ID[] = "AT+ID\r\n";
const char PROGMEM STR_MODE[] = "AT+MODE=LWOTAA\r\n";
const char PROGMEM STR_DR[] = "AT+DR=EU868\r\n";
const char PROGMEM STR_KEY[] = "AT+KEY=APPKEY,\"96395F2F6686099B84766352E937626E\"\r\n";
const char PROGMEM STR_CLASS[] = "AT+CLASS=A\r\n";
const char PROGMEM STR_PORT[] = "AT+PORT=8\r\n";
const char PROGMEM STR_JOIN[] = "AT+JOIN\r\n";

// ===== BUFFERS =====
static char recv_buf[200];
char rxBuffer[1024];
int rxIndex = 0;

// ===== STATE FLAGS =====
static bool lora_module_exists = false;
static bool lora_network_joined = false;
static bool BattV_Avg_is_low = false;

// ===== INTERRUPT VARIABLES =====
volatile bool buttonPressed = false;
unsigned long lastInterruptTime = 0;
unsigned long lastBatteryAlertTime = 0;

// ===== NETWORK CONFIG =====
byte mac[] = { 0xA8, 0x61, 0x0A, 0xAE, 0xD9, 0xAD };
const char* TCP_HOST = "150.100.100.20"; // Avec le PI : "192.168.1.1"; // Vraie API : 150.100.100.20 
const int TCP_PORT = 80; // Avec le Pi : 8765; // Mettre 80 pour l'API
EthernetClient ethClient;

// ===== Données des capteurs =====
float ms5637_pres = 0;  // MS5637 Data
uint16_t uv_voltage = 0; 
uint16_t uv_index = 0;
int rawValue = 0;
float voltage_mV = 0, radiation_Wm2 = 0;
// float voltage_mV_2 = 0, radiation_Wm2_2 = 0; // Pour un second pyranomètre
float api_vals[9] = {0};  // 9 values from API

// Variables globales pluviomètre
volatile int rain_pulses = 0;
float rain_mm = 0;
unsigned long last_rain_time = 0;

// ===== HARDWARE OBJECTS =====
SoftwareSerial loraSerial(2, 3);
DFRobot_UVIndex240370Sensor UVIndex240370Sensor(&Serial1);

// ===== TIMING =====
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 780000;  // Pour 13 minutes, modifiable 


// Permet d'afficher des séparateurs dans la console pour une meilleure lisibilité
void printSeparator() {
  Serial.println("========================================");
}

// Permet d'afficher des titres de sections dans la console pour une meilleure lisibilité
void printHeader(const char* title) {
  printSeparator();
  Serial.print("| ");
  Serial.print(title);
  Serial.println(" |");
  printSeparator();
}

// Permet d'afficher des messages de diagnostic avec un format uniforme
void printDiagnostic(const char* stage, const char* status) {
  #if ENABLE_DIAGNOSTICS
  Serial.print("[DIAG] ");
  Serial.print(stage);
  Serial.print(" : ");
  Serial.println(status);
  #endif
}

void rainGaugeISR() {
  unsigned long current_time = millis();
  if (current_time - last_rain_time > DEBOUNCE_TIME) {
    rain_pulses++;
    last_rain_time = current_time;
  }
}

// ============================================================================
// BUTTON INTERRUPT SERVICE ROUTINE
// ============================================================================

void buttonISR() {
  unsigned long currentTime = millis();
  
  // Anti-rebond matériel
  if (currentTime - lastInterruptTime >= BUTTON_COOLDOWN) {
    buttonPressed = true;
    lastInterruptTime = currentTime;
    
    Serial.println("\n[BUTTON] INTERRUPTION DÉTECTÉE - ENVOI DES DONNÉES IMMINENT !");
  } else {
    Serial.println("[BUTTON] Veuillez ne pas appuyer trop rapidement sur le bouton, merci ! ");
  }
}

// ============================================================================
// LORA & COMMUNICATION FUNCTIONS
// ============================================================================

/**
 * Send AT command from PROGMEM
 */
void sendProgmem(const char *cmd) {
  char tmp[80];
  strcpy_P(tmp, cmd);
  loraSerial.print(tmp);
  #if VERBOSE_MODE
  Serial.print("[TX] ");
  Serial.print(tmp);
  #endif
}

/**
 * Send AT command and check for expected response
 */
static int at_send_check_response(const char *p_ack, int timeout_ms, const char *p_cmd) {
    int ch, index = 0;
    memset(recv_buf, 0, 200);
    sendProgmem(p_cmd);
    delay(50);

    if (!p_ack) return 0;

    unsigned long start = millis();
    do {
        while (loraSerial.available()) {
            recv_buf[index++] = loraSerial.read();
            if(index >= 199) index = 0;
            #if VERBOSE_MODE
            Serial.write(recv_buf[index-1]);
            #endif
            delay(2);
        }
        if (strstr(recv_buf, p_ack)) {
          printDiagnostic("Réponse LoRa", "OK - ACK reçu");
          return 1;
        }
    } while (millis() - start < timeout_ms);
    
    printDiagnostic("Réponse LoRa", "TIMEOUT - No ACK");
    return 0;
}

// ============================================================================
// DATA ENCODING FUNCTIONS
// ============================================================================

/**
 * Convert float to integer with scale
 */
static long to_int(float value, int scale) {
    return (long)round(value * scale);
}

/**
 * Encode all sensor data to hexadecimal
 */
void encodeDataToHex(char* hexOutput) {
    printHeader("Processus d'encodage des données");
    
    Serial.println("\n[ENCODE] Facteurs d'échelle:");
    Serial.println("  - Échelle 100: Températures, Tensions, Énergies, Pressions");
    Serial.println("  - Échelle 10: Humidités, Pressions");
    Serial.println("  - Échelle 1: Puissance, Direction, Radiation");
    
    int scale100 = 100;
    int scale10 = 10;
    int scale1 = 1;

    // 14 uint16_t values: 9 from API + 1 from MS5637 + 2 from UV + 1 from Pyranometer + 1 from Pluviomètre
    uint16_t hex_vals[14] = {
      // API Data (9 values)
      (uint16_t)to_int(api_vals[0], scale100),  // [0] BattV_Avg (V)
      (uint16_t)to_int(api_vals[1], scale10),   // [1] AirT_C_Avg (°C)
      (uint16_t)to_int(api_vals[2], scale10),   // [2] RH (%)
      (uint16_t)to_int(api_vals[3], scale1),    // [3] SlrHoriz_W_Avg (W/m²)
      (uint16_t)to_int(api_vals[4], scale100),  // [4] SlrHoriz_MJ_Tot (MJ/m²)
      (uint16_t)to_int(api_vals[5], scale1),    // [5] SlrTilt_W_Avg (W/m²)
      (uint16_t)to_int(api_vals[6], scale100),  // [6] SlrTilt_MJ_Tot (MJ/m²)
      (uint16_t)to_int(api_vals[7], scale100),  // [7] WS_ms_S_WVT (m/s)
      (uint16_t)to_int(api_vals[8], scale1),    // [8] WindDir_D1_WVT (°)
      
      // MS5637 Data (1 value)
      (uint16_t)to_int(ms5637_pres, scale10),  // [9] MS5637_Pres (hPa/mbar)
      
      // UV Sensor Data (2 values)
      (uint16_t)to_int(uv_voltage, scale1),     // [10] UV_Voltage (mV)
      (uint16_t)to_int(uv_index, scale1),      // [11] UV_Index
      
      // Pyranometer Data (1 value)
      (uint16_t)to_int(radiation_Wm2, scale1),  // [12] Pyrano_Radiation (W/m²)
      
      // Données du pluviomètre
      (uint16_t)to_int(rain_mm, scale10),       // [13] Pluie_mm (mm)
    };
    
    // Affichage des valeurs avant conversion pour vérification
    Serial.println("\n[ENCODE] Values before hex conversion:");
    for(int i = 0; i < 14; i++) {
      Serial.print("  [");
      if(i < 10) Serial.print("0");
      Serial.print(i);
      Serial.print("] = ");
      Serial.print(hex_vals[i]);
      Serial.print(" -> 0x");
      if(hex_vals[i] < 0x1000) Serial.print("0");
      if(hex_vals[i] < 0x0100) Serial.print("0");
      if(hex_vals[i] < 0x0010) Serial.print("0");
      Serial.println(hex_vals[i], HEX);
    }
    
    // Conversion en hexadécimal (little-endian)
    Serial.println("\n[ENCODE] Conversion en hexadécimal (little-endian):");
    for(int i = 0; i < 14; i++) {
      uint16_t v = hex_vals[i];
      sprintf(&hexOutput[i*4], "%02X%02X", (v & 0xFF), (v >> 8));
    }
    hexOutput[56] = '\0';  // 14 * 4 = 56 characters (28 bytes)
    
    Serial.print("\n[ENCODE] Payload finale : ");
    Serial.println(hexOutput);
    Serial.print("[ENCODE] Longueur de la Payload : ");
    Serial.print(strlen(hexOutput));
    Serial.println(" characters (28 bytes)");
}

// ============================================================================
// Collecte des données par les capteurs
// ============================================================================

void readMS5637() {
  Serial.println("\nLecture de données du capteur MS5637...");
  
  if (!BaroSensor.isOK()) {
    BaroSensor.begin();  // Réinitialiser
    ms5637_pres = 0;
    Serial.print("  Erreur: ");
    Serial.println(BaroSensor.getError());
    printDiagnostic("MS5637", "Lecture échouée - Tentative de réinitialisation");
  } else {
    // Lecture OK
    ms5637_pres = BaroSensor.getPressure();
    
    Serial.print("  Temperature: ");
    Serial.print(BaroSensor.getTemperature(), 2);
    Serial.println(" °C");
    
    Serial.print("  Pressure: ");
    Serial.print(ms5637_pres, 2);
    Serial.println(" hPa/mbar");
    
    printDiagnostic("MS5637", "Lecture réussie");
  }
}

void readUVSensor() {
  Serial.println("\nLecture de données du capteur UV...");
  
  uv_voltage = UVIndex240370Sensor.readUvOriginalData();
  uv_index = UVIndex240370Sensor.readUvIndexData();
  
  Serial.print("  Voltage: ");
  Serial.print(uv_voltage);
  Serial.println(" mV");
  
  Serial.print("  UV Index: ");
  Serial.println(uv_index);
  
  printDiagnostic("Capteur UV", "Lecture réussie");
}

void readPyranometer() {
  Serial.println("\nLecture de données du capteur Pyranomètre...");
  
  rawValue = analogRead(PYRANO_PIN);
  voltage_mV = (rawValue / 1023.0) * 5000.0;
  radiation_Wm2 = voltage_mV * PYRANO_CALIBRATION;
  
  // Clamp to valid range
  if (radiation_Wm2 < 0) radiation_Wm2 = 0;
  if (radiation_Wm2 > 2000) radiation_Wm2 = 2000;
  
  Serial.print("  Raw ADC: ");
  Serial.println(rawValue);
  
  Serial.print("  Voltage: ");
  Serial.print(voltage_mV, 2);
  Serial.println(" mV");
  
  Serial.print("  Radiation Solaire: ");
  Serial.print(radiation_Wm2, 1);
  Serial.println(" W/m²");
  
  printDiagnostic("Pyranomètre", "Lecture réussie");
}

void readRainGauge() {
  Serial.println("\nLecture données du pluviomètre...");
  
  rain_mm = rain_pulses * RAIN_PER_PULSE;
  
  Serial.print("  Pulsations: ");
  Serial.println(rain_pulses);
  
  Serial.print("  Pluie: ");
  Serial.print(rain_mm, 2);
  Serial.println(" mm");
  
  // Réinitialiser pour le prochain cycle
  rain_pulses = 0;
  
  printDiagnostic("Pluviomètre", "Lecture réussie");
}

void readAllSensors() {
  printHeader("Collecte des données de tous les capteurs");
  readMS5637();
  readUVSensor();
  readPyranometer();
  readRainGauge();
  Serial.println();
}

// ============================================================================
// API DATA FETCHING FUNCTIONS
// ============================================================================

void displayAPIData() {
  Serial.println("\nDonnées météo reçues de l'API:");
  Serial.print("  [0] BattV_Avg: ");
  Serial.print(api_vals[0], 2);
  Serial.println(" V");
  
  Serial.print("  [1] AirT_C_Avg: ");
  Serial.print(api_vals[1], 2);
  Serial.println(" °C");
  
  Serial.print("  [2] RH: ");
  Serial.print(api_vals[2], 2);
  Serial.println(" %");
  
  Serial.print("  [3] SlrHoriz_W_Avg: ");
  Serial.print(api_vals[3], 2);
  Serial.println(" W/m²");
  
  Serial.print("  [4] SlrHoriz_MJ_Tot: ");
  Serial.print(api_vals[4], 2);
  Serial.println(" MJ/m²");
  
  Serial.print("  [5] SlrTilt_W_Avg: ");
  Serial.print(api_vals[5], 2);
  Serial.println(" W/m²");
  
  Serial.print("  [6] SlrTilt_MJ_Tot: ");
  Serial.print(api_vals[6], 2);
  Serial.println(" MJ/m²");
  
  Serial.print("  [7] WS_ms_S_WVT: ");
  Serial.print(api_vals[7], 2);
  Serial.println(" m/s");
  
  Serial.print("  [8] WindDir_D1_WVT: ");
  Serial.print(api_vals[8], 2);
  Serial.println(" °");
}

void fetchWeatherDataAPI() {
  printHeader("Collecte de données depuis l'API Météo");
  
  Serial.println("\n[API] Connexion au serveur...");
  Serial.print("  Host: ");
  Serial.print(TCP_HOST);
  Serial.print(":");
  Serial.println(TCP_PORT);
  
  if (!ethClient.connected()) {
    Serial.println("  Non connecté, initialisation d'une nouvelle connexion...");
    if (!ethClient.connect(TCP_HOST, TCP_PORT)) {
      printDiagnostic("API", "Connection échouée");
      delay(1000);
      return;
    }
    printDiagnostic("API", "Connection réussie");
    delay(500);
  }
  
  if (ethClient.connected()) {
    Serial.println("\nEnvoi de la requête HTTP...");
    ethClient.println("GET /command=DataQuery&uri=MeteoPau&format=json&mode=backfill&p1=600 HTTP/1.1"); // Vraie API : "http://150.100.100.20/command=DataQuery&uri=MeteoPau&format=json&mode=backfill&p1=600"
    ethClient.print("Host: ");
    ethClient.println(TCP_HOST);
    ethClient.println("Connection: close\r\n");
    printDiagnostic("API", "Requête envoyée");
  }
  
  delay(1000);
  
  rxIndex = 0;
  memset(rxBuffer, 0, 1024);
  
  Serial.println("\n[API] Lecture de la réponse HTTP...");
  unsigned long readStart = millis();
  while (ethClient.available()) {
    char c = ethClient.read();
    if (rxIndex < 1023) {
      rxBuffer[rxIndex++] = c;
    }
  }
  unsigned long readTime = millis() - readStart;
  rxBuffer[rxIndex] = '\0';

  Serial.print("  Taille de la réponse : ");
  Serial.print(rxIndex);
  Serial.println(" bytes");
  Serial.print("  Temps de lecture: ");
  Serial.print(readTime);
  Serial.println(" ms");
  
  #if VERBOSE_MODE
  Serial.println("\n[API] Réponse raw (LAST 150 chars):");
  int start = (rxIndex > 150) ? rxIndex - 150 : 0;
  for(int i = start; i < rxIndex; i++) {
    Serial.write(rxBuffer[i]);
  }
  Serial.println("\n");
  #endif
  
  debugAPIResponse();

  Serial.println("[API] Parsing des données JSON...");
  parseWeatherData(rxBuffer);
  
  displayAPIData();
  
  ethClient.stop();
  printDiagnostic("API", "Connection fermée");
}

void parseWeatherData(const char* json) {
  printDiagnostic("Parser", "Recherche de la structure JSON...");
  
  // Cherche soit "data" (ancien format) soit "rows" (nouveau format)
  const char* valsSource = strstr(json, "\"data\":");
  if (!valsSource) {
    valsSource = strstr(json, "\"rows\":");
    if (!valsSource) {
      printDiagnostic("Parser", "ERREUR - Aucun tableau 'data' ou 'rows' trouvé");
      return;
    }
    printDiagnostic("Parser", "'rows' array found (NEW FORMAT) ");
  } else {
    printDiagnostic("Parser", "'data' array found (OLD FORMAT) ");
  }
  
  // Cherche le premier [ (tableau de données)
  const char* arrayStart = strstr(valsSource, "[");
  if (!arrayStart) {
    printDiagnostic("Parser", "ERREUR - Pas de tableau trouvé");
    return;
  }
  
  // Cherche le second [ (les valeurs réelles)
  arrayStart = strstr(arrayStart + 1, "[");
  if (!arrayStart) {
    printDiagnostic("Parser", "ERREUR - Pas de tableau de valeurs trouvé");
    return;
  }
  
  arrayStart += 1;  // Skip the [
  
  int valIndex = 0;
  char numStr[20];
  int numIndex = 0;
  int skipCount = 0;  // Pour skipper les 3 premiers éléments (id, time, no)
  
  Serial.println("\n  Extraction des valeurs:");
  
  // Initialiser toutes les valeurs à 0
  for(int i = 0; i < 9; i++) {
    api_vals[i] = 0.0;
  }
  
  // Parser la chaîne
  for (int i = 0; arrayStart[i]; i++) {
    char c = arrayStart[i];
    
    if (c == ']') {
      // Traiter la dernière valeur si elle existe
      if (numIndex > 0) {
        numStr[numIndex] = '\0';
        
        // Skipper les 3 premiers éléments
        if (skipCount >= 3 && valIndex < 9) {
          api_vals[valIndex] = atof(numStr);
          
          Serial.print("    [");
          if(valIndex < 10) Serial.print("0");
          Serial.print(valIndex);
          Serial.print("] = ");
          Serial.println(numStr);
          
          valIndex++;
        }
        skipCount++;
      }
      break;
    }
    
    // Parser les nombres
    if ((c >= '0' && c <= '9') || c == '.' || c == '-') {
      if (numIndex < 19) numStr[numIndex++] = c;
    }
    // Séparateur (virgule)
    else if (c == ',' && numIndex > 0) {
      numStr[numIndex] = '\0';
      
      // Skipper les 3 premiers éléments (id, time, no)
      if (skipCount >= 3 && valIndex < 9) {
        api_vals[valIndex] = atof(numStr);
        
        Serial.print("    [");
        if(valIndex < 10) Serial.print("0");
        Serial.print(valIndex);
        Serial.print("] = ");
        Serial.println(numStr);
        
        valIndex++;
      }
      skipCount++;
      numIndex = 0;
    }
  }
  
  Serial.print("\n[Parser] Extraction complete - ");
  Serial.print(valIndex);
  Serial.println(" valeurs extraites ✓");
}

// ============================================================================
// BATTERY ALERT FUNCTION 
// ============================================================================

void sendBatteryAlert() {
  printHeader("===== ALERTE BATTERIE FAIBLE - ENVOI D'URGENCE =====");
  
  Serial.println("\n[ALERTE] BATTERIE FAIBLE!");
  Serial.print("[ALERTE] Tension moyenne : ");
  Serial.print(api_vals[0], 2);
  Serial.println(" V");
  
  // Créer un payload d'alerte SIMPLIFIÉ: seulement batterie + code alerte
  // 2 uint16_t: batterie (scale 100) + code alerte
  char alertPayload[17];  // 8 bytes = 16 caractères hex + 1 null terminator
  
  uint16_t battery_val = (uint16_t)to_int(api_vals[0], 100);  // Batterie avec scale 100
  uint16_t alert_code = ALERT_BATTERY_LOW;  // 0xFF01
  
  // Encoder en little-endian
  sprintf(alertPayload, "%02X%02X%02X%02X", 
    (battery_val & 0xFF), (battery_val >> 8),
    (alert_code & 0xFF), (alert_code >> 8)
  );
  
  Serial.print("[ALERTE] Payload: ");
  Serial.println(alertPayload);
  Serial.print("[ALERTE] Longueur: ");
  Serial.print(strlen(alertPayload));
  Serial.println(" characters (8 bytes)");
  
  // Transmettre l'alerte
  printHeader("Transmission de l'alerte batterie via LoRa");
  
  Serial.println("\nPréparation de la transmission LoRa...");
  Serial.print("  Payload: ");
  Serial.println(alertPayload);
  
  char cmd[96];
  sprintf(cmd, "AT+CMSGHEX=\"%s\"\r\n", alertPayload);
  
  Serial.println("\n[LoRa] Envoi de la commande AT...");
  loraSerial.print(cmd);
  
  Serial.println("\n[LoRa] Attente de la confirmation de transmission...");
  if (at_send_check_response("Done", 5000, "")) {
    printDiagnostic("LoRa TX ALERTE", "Transmission réussie");
  } else {
    printDiagnostic("LoRa TX ALERTE", "Transmission échouée");
  }
  
  Serial.println();
}


// ============================================================================
// LORA TRANSMISSION
// ============================================================================

void transmitDataLoRa(const char* hexPayload) {
  printHeader("Transmission des données via LoRa");
  
  Serial.println("\nPréparation de la transmission LoRa...");
  Serial.print("  Payload: ");
  Serial.println(hexPayload);
  Serial.print("  Longueur de la Payload: ");
  Serial.print(strlen(hexPayload));
  Serial.println(" characters");
  
  char cmd[96];
  sprintf(cmd, "AT+CMSGHEX=\"%s\"\r\n", hexPayload);
  
  Serial.println("\n[LoRa] Envoi de la commande AT...");
  Serial.print("  Commande: ");
  Serial.println(cmd);
  
  loraSerial.print(cmd);
  
  Serial.println("\n[LoRa] Attente de la confirmation de transmission...");
  if (at_send_check_response("Done", 5000, "")) {
    printDiagnostic("LoRa TX", "Transmission réussie");
  } else {
    printDiagnostic("LoRa TX", "Transmission échoué ou timeout");
  }
  
  Serial.println();
}

// ============================================================================
// I2C SCANNING
// ============================================================================

void testI2C() {
  Serial.println("Scan des périphériques I2C...");
  
  Wire.begin();
  int devices = 0;
  for(byte i = 8; i < 120; i++) {
    Wire.beginTransmission(i);
    if(Wire.endTransmission() == 0) {
      Serial.print("  Périphérique I2C trouvé à 0x");
      Serial.println(i, HEX);
      devices++;
    }
  }
  
  Serial.print("Trouvés ");
  Serial.print(devices);
  Serial.println(" Périphériques I2C\n");
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  printHeader("===== Démarrage du Diagnostic =====");
  
  printDiagnostic("Système", "Boot initialisé");
  
  // ===== BUTTON INIT =====
  Serial.println("\n[BUTTON] Initialisation du bouton d'urgence sur la broche 7...");
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, FALLING);
  printDiagnostic("BUTTON", "Initialisé avec interruption matérielle");
  
  // ===== SERIAL1 INIT =====
  Serial.println("\n[UV Sensor] Initialisation sur Serial1 (D0-D1)...");
  Serial1.begin(9600);
  delay(100);
  printDiagnostic("Serial1 UV", "OK");
  
  // ===== SOFTWARESERIAL INIT =====
  Serial.println("\n[SOFTWARESERIAL] Initialisation sur les broches 2-3...");
  loraSerial.begin(9600);
  delay(100);
  printDiagnostic("SoftwareSerial", "OK");
  
  // ===== ETHERNET SHIELD INIT =====
  Serial.println("\n[ETHERNET] Initialisation du Shield Ethernet...");
  Serial.println("  Réinitialisation de la broche CS (broche 10)...");
  pinMode(10, OUTPUT);
  digitalWrite(10, LOW);
  delay(100);
  digitalWrite(10, HIGH);
  delay(500);
  printDiagnostic("Ethernet", "Réinitialisation de la broche CS terminée");
  
  Serial.println("\n[ETHERNET] Configuration de l'IP Statique...");

  // ===== CONFIGURATION IP STATIQUE =====
  IPAddress ip(150, 100, 100, 67);                 // IP Arduino Pour API : 150.100.100.67 
  IPAddress gateway(150, 100, 100, 20);            // Passerelle (votre routeur) Pour API : 150.100.100.20
  IPAddress subnet(255, 255, 255, 0);              // Masque de sous-réseau
  IPAddress dns(150, 100, 100, 20);                // DNS (votre routeur) Pour API : 150.100.100.20
  Ethernet.begin(mac, ip, dns, gateway, subnet);
  
  Serial.print("  Adresse IP : ");
  Serial.println(Ethernet.localIP());
  

  Serial.print("  Adresse IP (statique): ");
  Serial.println(Ethernet.localIP());
  Serial.print("  Passerelle: ");
  Serial.println(gateway);
  Serial.print("  Masque: ");
  Serial.println(subnet);
  Serial.print("  DNS: ");
  Serial.println(dns);

  printDiagnostic("Ethernet", "Adresse IP statique configurée");
  
  // ===== I2C INIT =====
  Serial.println("\n[I2C] Démarrage de Wire (broches SDA/SCL)...");
  Wire.begin();
  delay(100);
  printDiagnostic("I2C", "Initialisé");
  
  testI2C();
  
  // ===== MS5637 INIT =====
  Serial.println("[MS5637] Initialisation du capteur...");
  int ms5637_attempts = 0;
  while (!BaroSensor.isOK() && ms5637_attempts < 20) {
    Serial.print(".");
    BaroSensor.begin();
    ms5637_attempts++;
    delay(1000);
  }
  if (ms5637_attempts < 20) {
    printDiagnostic("MS5637", "Initialisé avec succès");
  } else {
    printDiagnostic("MS5637", "ÉCHEC DE L'INITIALISATION après 20 tentatives");
  }
  
  // ===== UV SENSOR INIT =====
  Serial.println("[Capteur UV] Initialisation du capteur...");
  int uv_attempts = 0;
  while(!UVIndex240370Sensor.begin() && uv_attempts < 20) {
    Serial.print(".");
    uv_attempts++;
    delay(1000);
  }
  if (uv_attempts < 20) {
    printDiagnostic("Capteur UV", "Initialisé avec succès");
  } else {
    printDiagnostic("Capteur UV", "ÉCHEC DE L'INITIALISATION après 20 tentatives");
  }

  // ===== RAIN GAUGE INIT =====
  Serial.println("\n[Pluviomètre] Initialisation du Pluviomètre...");
  pinMode(RAIN_GAUGE_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(RAIN_GAUGE_PIN), rainGaugeISR, FALLING);
  printDiagnostic("Pluviomètre", "Pluviomètre initialisé sur le pin 8");
  
  // ===== PYRANOMETER TEST =====
  Serial.println("\n[Pyranomètre] Test de l'input analogue...");
  int pyrano_raw = analogRead(PYRANO_PIN);
  float pyrano_voltage = (pyrano_raw / 1023.0) * 5000.0;
  Serial.print("  Raw ADC: ");
  Serial.println(pyrano_raw);
  Serial.print("  Voltage: ");
  Serial.print(pyrano_voltage, 2);
  Serial.println(" mV");
  printDiagnostic("Pyranomètre", "Analog input OK");
  
  // ===== WIO-E5 LORA MODULE INIT =====
  Serial.println("\n[WIO-E5] Test de la connexion LoRa au module..");
  if (at_send_check_response("+AT: OK", 200, STR_AT)) {
    lora_module_exists = true;
    printDiagnostic("Wio-E5", "Module trouvé et répondant");
    
    Serial.println("\n[WIO-E5] Envoi des commandes de configuration...");
    
    Serial.println("  [1/6] ID du module...");
    at_send_check_response("+ID:", 1000, STR_ID);
    
    Serial.println("  [2/6] Mode LWOTAA...");
    at_send_check_response("+MODE: LWOTAA", 1000, STR_MODE);
    
    Serial.println("  [3/6] Région configurée à  EU868...");
    at_send_check_response("+DR:", 1000, STR_DR);
    
    Serial.println("  [4/6] Configuration de l'APP key...");
    at_send_check_response("+KEY: APPKEY", 1000, STR_KEY);
    
    Serial.println("  [5/6] Configuration Classe A...");
    at_send_check_response("+CLASS:", 1000, STR_CLASS);
    
    Serial.println("  [6/6] Configuration du port 8...");
    at_send_check_response("+PORT:", 1000, STR_PORT);
    
    lora_network_joined = true;
    printDiagnostic("Wio-E5", "Configuration terminée");
  } else {
    lora_module_exists = false;
    printDiagnostic("Wio-E5", "Module non trouvé ou ne répond pas");
  }
  printHeader("===== Setup Complete =====");
  
  lastSendTime = millis();
}

void debugAPIResponse() {
  printHeader("DEBUG: API RESPONSE ANALYSIS");
  
  Serial.println("\n[DEBUG] Response Statistics:");
  Serial.print("  Total bytes: ");
  Serial.println(rxIndex);
  
  Serial.println("\n[DEBUG] COMPLETE RAW RESPONSE:");
  Serial.println("---START---");
  for(int i = 0; i < rxIndex; i++) {
    Serial.write(rxBuffer[i]);
  }
  Serial.println("\n---END---");
  
  Serial.println("\n[DEBUG] JSON PART ONLY:");
  const char* jsonStart = strstr(rxBuffer, "{");
  if (jsonStart) {
    int indent = 0;
    bool inString = false;
    for(int i = 0; jsonStart[i]; i++) {
      char c = jsonStart[i];
      
      if (c == '"') {
        inString = !inString;
      }
      
      if (!inString) {
        if (c == '{' || c == '[') {
          Serial.write(c);
          Serial.write('\n');
          indent += 2;
          for(int j = 0; j < indent; j++) Serial.write(' ');
        }
        else if (c == '}' || c == ']') {
          Serial.write('\n');
          indent = (indent > 2) ? indent - 2 : 0;
          for(int j = 0; j < indent; j++) Serial.write(' ');
          Serial.write(c);
        }
        else if (c == ',') {
          Serial.write(',');
          Serial.write('\n');
          for(int j = 0; j < indent; j++) Serial.write(' ');
        }
        else if (c == ':') {
          Serial.write(": ");
        }
        else if (c != ' ' && c != '\n' && c != '\r' && c != '\t') {
          Serial.write(c);
        }
      } else {
        Serial.write(c);
      }
    }
    Serial.println("\n");
  } else {
    Serial.println("ERROR: No JSON found!");
  }
  
  Serial.println("\n[DEBUG] JSON Structure:");
  int braces = 0, brackets = 0;
  for(int i = 0; i < rxIndex; i++) {
    if (rxBuffer[i] == '{') braces++;
    if (rxBuffer[i] == '}') braces--;
    if (rxBuffer[i] == '[') brackets++;
    if (rxBuffer[i] == ']') brackets--;
  }
  Serial.print("  Brace balance: ");
  Serial.println(braces);
  Serial.print("  Bracket balance: ");
  Serial.println(brackets);
  
  if (braces == 0 && brackets == 0) {
    Serial.println("    structure Json valide");
  } else {
    Serial.println("    structure Json invalide");
  }
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  if(!lora_module_exists) {
    delay(2000);
    return;
  }

  // ===== BUTTON CHECK (POLLING) =====
  static unsigned long lastButtonTime = 0;
  static bool buttonWasPressed = false;
  
  if (digitalRead(BUTTON_PIN) == HIGH) {  // ← HIGH quand appuyé (car INPUT_PULLUP)
    // Bouton appuyé
    if (!buttonWasPressed && (millis() - lastButtonTime >= BUTTON_COOLDOWN)) {
      buttonPressed = true;
      lastButtonTime = millis();
      buttonWasPressed = true;
      Serial.println("\n[BUTTON] INTERRUPTION DÉTECTÉE - ENVOI DES DONNÉES IMMINENT !");
    }
  } else {
    // Bouton relâché
    buttonWasPressed = false;
  }

  // ===== LORA NETWORK JOIN =====
  if (lora_network_joined) {
    Serial.println("\n[LoRa] Tentative de connexion au reseau...");
    
    char tmp[80];
    strcpy_P(tmp, STR_JOIN);
    loraSerial.print(tmp);
    
    memset(recv_buf, 0, 200);
    delay(100);
    
    int index = 0;
    unsigned long start = millis();
    bool network_joined = false;
    
    while (millis() - start < 12000) {
      while (loraSerial.available()) {
        recv_buf[index++] = loraSerial.read();
        if(index >= 199) index = 0;
        #if VERBOSE_MODE
        Serial.write(recv_buf[index-1]);
        #endif
        delay(2);
      }
      
      if (strstr(recv_buf, "+JOIN: Network joined") || 
          strstr(recv_buf, "+JOIN: Joined already")) {
        network_joined = true;
        break;
      }
      
      if (strstr(recv_buf, "+JOIN: Join failed")) {
        printDiagnostic("LoRa", "Join failed - Nouvelle tentative");
        lora_network_joined = true;
        delay(10000);
        return;
      }
    }
    
    if (network_joined) {
      lora_network_joined = false;
      printDiagnostic("LoRa", "Connexion au réseau réussie ");
      Serial.println("[LoRa] Passage à la boucle de collecte de données\n");
    } else {
      printDiagnostic("LoRa", "Timeout - Nouvelle tentative dans 10s");
      delay(10000);
      return;
    }
  }
  
  // ===== COLLECTE DE DONNÉES (NORMALE OU FORCÉE PAR INTERRUPTION) =====
  bool shouldCollect = false;
  
  // Cas 1: Bouton pressé (interruption)
  if (buttonPressed) {
    shouldCollect = true;
    buttonPressed = false;  // Réinitialiser le flag
    printHeader("===== ENVOI D'URGENCE (INTERRUPTION) =====");
  }
  
  // Cas 2: Intervalle de 3 minutes écoulé (envoi régulier)
  else if (millis() - lastSendTime >= SEND_INTERVAL) {
    shouldCollect = true;
    printHeader("===== Cycle régulier (3 minutes) =====");
  }
  
  // Exécuter l'envoi si l'une des conditions est vraie
  if (shouldCollect) {
    lastSendTime = millis();
    
    Serial.print("[CYCLE] Timestamp: ");
    Serial.println(millis());
    Serial.println("[CYCLE] Lecture de toutes les sources de donnees...\n");
    
    // Fetch API data
    fetchWeatherDataAPI();
    
    // Read all sensors
    readAllSensors();

    if (api_vals[0] < 12.0) {
      BattV_Avg_is_low = true;
      
      if (millis() - lastBatteryAlertTime >= 300000) {  // 5 minutes
        sendBatteryAlert();
        lastBatteryAlertTime = millis();
        delay(2000);
        printHeader("===== Alerte batterie envoyée =====");
      } else {
        printDiagnostic("BATTERIE", "Alerte déjà envoyée récemment");
      }
    } else {
      BattV_Avg_is_low = false;
    }
    // Encode data to hex
    char hexPayload[57];  // 56 + 1 for null terminator
    encodeDataToHex(hexPayload);
    
    // Transmit via LoRa
    transmitDataLoRa(hexPayload);
    
    printHeader("===== Cycle Terminé, le prochain cycle commence et se terminera dans 3 minutes =====");
  }

  delay(100);
}