#!/usr/bin/sh
# TOM7 Installer / Updater / Uninstaller

set -euo pipefail

appName="tomcatc2"
installDir="/opt/$appName"
binPath="/usr/local/bin/$appName"

RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
BOLD="\e[1m"
RESET="\e[0m"

installApp() {
    echo -e "${BLUE}[+] Installing $appName...${RESET}"
    sudo mkdir -p "$installDir"
    sudo cp -r ./* "$installDir"
    echo "#!/usr/bin/bash
    bash \"$installDir/tomcatc2.sh\" \"\$@\"" | sudo tee "$binPath" > /dev/null
    sudo chmod +x "$binPath"
    echo -e "${GREEN}[+] Installation Complete!${RESET}"
    echo -e "You Can Now Run: ${BOLD}$appName${RESET}"
}

updateApp() {
    if [ ! -d "$installDir" ]; then
        echo -e "${RED}[+] No Existing Installation Found. Please Install First.${RESET}"
        exit 1
    fi
    echo -e "${YELLOW}[+] Updating $appName At $installDir...${RESET}"
    sudo rm -rf "$installDir"
    sudo mkdir -p "$installDir"
    sudo cp -r ./* "$installDir"
    echo -e "${GREEN}[+] Update Complete!${RESET}"
}

uninstallApp() {
    if [ ! -d "$installDir" ]; then
        echo -e "${RED}[!] $appName Is Not Installed.${RESET}"
        exit 1
    fi
    echo -e "${YELLOW}⚠ Are You Sure Want To Uninstall $appName? (y/n)${RESET}"
    read -rp "~>> " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}[-] Removing Files...${RESET}"
        sudo rm -rf "$installDir" "$binPath"
        echo -e "${GREEN}[+] $appName Has Been Uninstalled.${RESET}"
    else
        echo -e "${BLUE}[x] Uninstall Canceled.${RESET}"
    fi
}

clear
echo "$appName — Installer / Updater / Uninstaller"
echo
echo "Select an option:"
echo "1.~> Install"
echo "2.~> Update"
echo "3.~> Uninstall"
echo "4.~> Exit"
echo
read -rp "Enter Options ~>> " choice
echo

case "$choice" in
    1)
        installApp;;
    2)
        updateApp;;
    3)
        uninstallApp;;
    4)
        echo "Exiting..."
        exit 0;;
    *)
        echo -e "${RED}Invalid Options.${RESET}"
        exit 1;;
esac

echo
read -rp "Press Enter To Close..."
