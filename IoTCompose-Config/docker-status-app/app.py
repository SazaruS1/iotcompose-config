from flask import Flask, jsonify, send_from_directory
import json

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/status")
def status():
    try:
        import socket
        
        # Se connecter au socket Docker
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect('/var/run/docker.sock')
        
        # Envoyer la requête HTTP
        request = b'GET /containers/json?all=true HTTP/1.0\r\nHost: localhost\r\n\r\n'
        sock.sendall(request)
        
        # Récupérer la réponse
        response = b''
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        sock.close()
        
        # Parser la réponse
        response_str = response.decode('utf-8')
        json_start = response_str.find('[')
        json_data = response_str[json_start:]
        containers_raw = json.loads(json_data)
        
        containers = []
        for c in containers_raw:
            status_str = c.get('State', 'unknown')
            containers.append({
                "name": c.get('Names', ['unknown'])[0].lstrip('/'),
                "image": c.get('Image', 'unknown'),
                "status": status_str
            })
        
        containers.sort(key=lambda x: x["name"])
        return jsonify(containers)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777)
