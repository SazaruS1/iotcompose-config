#include <SPI.h>
#include <Ethernet.h>

// Configuration réseau
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(150,100,100,67);  // IP de votre Arduino (ajustez selon votre réseau) 150.100.100.21

// Configuration du serveur CR1000
const char* server = "150.100.100.20";       // "150.100.100.20";
const int port = 80;                         //  80;

EthernetClient client;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Attendre que le port série soit prêt
  }

  Serial.println(F("==========================================="));
  Serial.println(F("| Diagnostic API CR1000 Datalogger        |"));
  Serial.println(F("==========================================="));
  
  // Initialiser Ethernet
  Serial.println(F("\n[ETHERNET] Initialisation..."));
  if (Ethernet.begin(mac) == 0) {
    Serial.println(F("[ERREUR] DHCP échoué, utilisation IP statique"));
    Ethernet.begin(mac, ip);
  }
  
  Serial.print(F("  Adresse IP Arduino: "));
  Serial.println(Ethernet.localIP());
  
  delay(1000);  // Laisser le temps à Ethernet de se stabiliser
  
  // Tester la connexion à l'API
  testApiConnection();
}

void loop() {
  // Répéter le test toutes les 60 secondes
  delay(60000);
  testApiConnection();
}

void testApiConnection() {
  Serial.println(F("\n==========================================="));
  Serial.println(F("| Test de connexion à l'API              |"));
  Serial.println(F("==========================================="));
  
  Serial.print(F("\n[API] Connexion à "));
  Serial.print(server);
  Serial.print(F(":"));
  Serial.println(port);
  
  if (client.connect(server, port)) {
    Serial.println(F("[OK] Connecté au serveur "));
    
    // Envoyer la requête HTTP GET
    Serial.println(F("\n[HTTP] Envoi de la requête..."));
    client.println(F("GET /?command=DataQuery&uri=MeteoPau&format=json&mode=backfill&p1=600 HTTP/1.1"));
    client.print(F("Host: "));
    client.println(server);
    client.println(F("Connection: close"));
    client.println();
    
    Serial.println(F("[OK] Requête envoyée"));
    
    // Attendre la réponse
    Serial.println(F("\n[HTTP] Attente de la réponse..."));
    unsigned long timeout = millis();
    while (client.available() == 0) {
      if (millis() - timeout > 5000) {
        Serial.println(F("[ERREUR] Timeout - Aucune réponse du serveur"));
        client.stop();
        return;
      }
    }
    
    Serial.println(F("[OK] Réponse reçue\n"));
    
    // Lire et afficher la réponse complète
    Serial.println(F("==========================================="));
    Serial.println(F("| RÉPONSE COMPLÈTE DU SERVEUR             |"));
    Serial.println(F("==========================================="));
    Serial.println();
    
    bool isJsonStarted = false;
    int braceCount = 0;
    String jsonBuffer = "";
    
    while (client.available()) {
      char c = client.read();
      
      // Afficher tous les caractères (headers + JSON)
      Serial.print(c);
      
      // Détecter le début du JSON
      if (c == '{') {
        isJsonStarted = true;
        braceCount++;
      }
      
      // Compter les accolades pour détecter la fin du JSON
      if (isJsonStarted) {
        jsonBuffer += c;
        if (c == '}') {
          braceCount--;
        } else if (c == '{') {
          // Déjà compté au début
        }
      }
    }
    
    Serial.println();
    Serial.println(F("==========================================="));
    Serial.println(F("| FIN DE LA RÉPONSE                       |"));
    Serial.println(F("==========================================="));
    
    // Afficher des statistiques
    Serial.println(F("\n[STATS] Statistiques de la réponse:"));
    Serial.print(F("  Taille du JSON: "));
    Serial.print(jsonBuffer.length());
    Serial.println(F(" caractères"));
    Serial.print(F("  Balance des accolades: "));
    Serial.println(braceCount);
    
    if (braceCount == 0) {
      Serial.println(F("  [OK] Structure JSON valide"));
    } else {
      Serial.println(F("  [ATTENTION] Structure JSON possiblement incomplète"));
    }
    
    client.stop();
    Serial.println(F("\n[API] Connexion fermée"));
    
  } else {
    Serial.println(F("[ERREUR] Impossible de se connecter au serveur"));
    Serial.println(F("  Vérifiez:"));
    Serial.println(F("  - L'adresse IP du CR1000 (150.100.100.20)"));
    Serial.println(F("  - La connexion réseau"));
    Serial.println(F("  - Les paramètres de l'API"));
  }
}