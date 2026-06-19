#!/usr/bin/env python3
#// Pour activer la fausse API, on se place dans le bon dossier et on fait : 
#// // source venv/bin/activate
#// Sur le PC : python3 ServeurAPI_3.py + Désactiver le Pare-Feu Sur le PI : python3 api_test_server.py 

"""
Serveur HTTP simulant l'API DataQuery d'un CR1000 Datalogger.
Utilise HTTP
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import random
from datetime import datetime, timedelta

class WeatherAPIHandler(BaseHTTPRequestHandler):
    """Gère les requêtes HTTP dans le style du CR1000 Datalogger"""
    
    # Compteur de records global
    record_counter = 0
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Traite les requêtes GET"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        command = query_params.get('command', [None])[0]
        uri = query_params.get('uri', [None])[0]
        mode = query_params.get('mode', ['most-recent'])[0]
        p1 = query_params.get('p1', ['10'])[0]
        format_type = query_params.get('format', ['json'])[0]
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.client_address[0]} - command={command}, uri={uri}, mode={mode}, p1={p1}")
        
        try:
            if command == 'DataQuery' and uri == 'MeteoPau':
                response = self.handle_dataquery(mode, p1, format_type)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response.encode())
            else:
                self.send_error(400, "Unsupported command or URI")
        except Exception as e:
            print(f"Erreur: {e}")
            self.send_error(500, str(e))
    
    def handle_dataquery(self, mode, p1, format_type):
        """Génère une réponse DataQuery conforme à la doc Campbell Scientific"""
        
        num_records = int(p1) if mode == 'most-recent' else 10
        
        records = []
        WeatherAPIHandler.record_counter += 1
        
        for i in range(num_records):
            WeatherAPIHandler.record_counter += 1
            record_id = WeatherAPIHandler.record_counter
            
            # Timestamp
            timestamp = (datetime.now() - timedelta(minutes=num_records - i)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Données cohérentes
            record = [
                record_id,                                     # id
                timestamp,                                     # time
                record_id,                                     # no (numéro séquentiel)
                round(random.uniform(11.5, 13.5), 2),          # Tension moyenne de la batterie 'BattV_Avg' (Nombre réel)             Unité : Volt (V)
                round(random.uniform(10, 25), 1),              # Temperature moyenne de l'air 'AitT_C_Avg' (Nombre réel)              Unité : °C (degré Celsius)
                round(random.uniform(30, 90), 1),              # Humidité relative 'RH' (Nombre réel) RH (%, humidité relative)       Unité : %
                round(random.uniform(0, 900), 1),              # Puissance solaire moyenne horizontale 'SlrHoriz_W_Avg' (Nombre réel) Unité : W/m² (puissance solaire horiz.)
                round(random.uniform(0, 10), 2),               # Energie solaire totale horizontale 'SlrHoriz_MJ_Tot' (Nombre réel)   Unité : MJ/m² (énergie solaire horiz.)
                round(random.uniform(0, 1000), 1),             # Puissance solaire moyenne verticale 'SlrTilt_W_Avg' (Nombre réel)    Unité : W/m² (puissance solaire verticale)
                round(random.uniform(0, 12), 2),               # Energie solaire totale verticale 'SlrTilt_MJ_Tot' (Nombre réel)      Unité : MJ/m² (énergie solaire verticale)
                round(random.uniform(0, 15), 2),               # Vitesse du vent moyenne 'WS_ms_S_WVT' (Nombre réel)                  Unité : m/s (vitesse du vent)
                round(random.uniform(0, 360), 1),              # Direction du vent en degrés 'WindDir_D1_WVT' (Nombre réel)           Unité : degrès (direction du vent)
            ]
            records.append(record)
        
        # Format conforme à la doc Campbell Scientific
        response = {
            "table": {
                "name": "MeteoPau",
                "fields": [
                    "id", "time", "no", 
                    "BattV_Avg", "AirT_C_Avg", "RH",
                    "SlrHoriz_W_Avg", "SlrHoriz_MJ_Tot", 
                    "SlrTilt_W_Avg", "SlrTilt_MJ_Tot",
                    "WS_ms_S_WVT", "WindDir_D1_WVT"
                ],
                "rows": records
            }
        }
        
        return json.dumps(response, indent=2)

def main():
    server_address = ("0.0.0.0", 5000)
    httpd = HTTPServer(server_address, WeatherAPIHandler)
    print(f"Serveur HTTP simulant l'API CR1000 Datalogger sur http://0.0.0.0:5000")
    print(f" Accessible depuis Arduino: http://192.168.1.10:5000")
    print(f"Essai local : http://localhost:5000/?command=DataQuery&uri=MeteoPau&format=json&mode=most-recent&p1=1") # Vraie API : "http://150.100.100.20/command=DataQuery&uri=MeteoPau&format=json&mode=backfill&p1=600"
    print(f"En attente de requêtes...\n")
    httpd.serve_forever()

if __name__ == "__main__":
    main()