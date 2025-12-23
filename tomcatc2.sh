#!/usr/bin/sh
# TOMCAT-C2 Starter

set -euo pipefail

baseDir="$(dirname "$(realpath "$0")")"
scriptDir="$baseDir/"

CMD1="$scriptDir/SERVER/tomcatv1s.py"
CMD2="$scriptDir/FlaskServer/tomcatv1fs.py"
CMD3="$scriptDir/AGENT/tomcatv1a.py"
CMD4="$scriptDir/AGENT/mintomcatv1a.py"

BOLD=$(tput BOLD 2>/dev/null || echo "")
NORMAL=$(tput sgr0 2>/dev/null || echo "")
GREEN=$(tput setaf 2 2>/dev/null || echo "")
RED=$(tput setaf 1 2>/dev/null || echo "")
CYAN=$(tput setaf 6 2>/dev/null || echo "")
YELLOW=$(tput setaf 3 2>/dev/null || echo "")
RESET="${NORMAL}"

TERMINAL=""
for t in gnome-terminal konsole xfce4-terminal mate-terminal tilix alacritty x-terminal-emulator; do
    if command -v "$t" >/dev/null 2>&1; then
        TERMINAL="$t"
        break
    fi
done
if [ -z "$TERMINAL" ]; then
    echo "${RED} [!] ${YELLOW} No Supported Terminal Emulator Found! ${RESET}"
    exit 1
fi

banner() {
    xbanner="""
            ___________________      _____  _________     ________________ _________  ________
            \\__    ___/\\_____  \\    /     \\ \\_   ___ \\   /  _  \\__    ___/ \\_   ___ \\ \\_____  \\
              |    |    /   |   \\  /  \\ /  \\/    \\  \\/  /  /_\\  \\|    |    /    \\  \\/  /  ____/
              |    |   /    |    \\/    Y    \\     \\____/    |    \\    |    \\     \\____/       \\
              |____|   \\_______  /\\____|__  /\\______  /\\____|__  /____|     \\______  /\\_______ \\
                               \\/         \\/        \\/         \\/                  \\/         \\/
                    ~>> Author: TOM7
                    ~>> GitHub: tom7voldemort
                    ~>> Born For Exploitation
    """
    clear
    if command -v lolcat >/dev/null 2>&1; then
        echo -e "$xbanner" | lolcat
    else
        echo "${RED} $xbanner ${RESET}"
    fi
    echo
}

launchTerminal() {
    local scriptPath="$1"
    local sudoProcess="${2:-false}"

    if [ ! -f "$scriptPath" ]; then
        echo "${RED} [!] ${YELLOW} Script Not Found: ${RED} $scriptPath ${RESET}"
        sleep 2
        return
    fi
    if [[ "$scriptPath" == *.py ]]; then
        cmd="python3 \"$scriptPath\""
    elif [[ "$scriptPath" == *.sh ]]; then
        cmd="chmod +x *.sh && bash \"$scriptPath\""
    fi
    if [ "$sudoProcess" = true ]; then
        cmd="sudo $cmd"
    fi
    echo "${GREEN} >>> ${CYAN} Launching ${GREEN} >>>: ${YELLOW} $scriptPath ${RESET}"

    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal -- bash -c "$cmd; echo; read -p 'Press Enter to close...'";;
        konsole)
            konsole -e bash -c "$cmd; echo; read -p 'Press Enter to close...'";;
        xfce4-terminal)
            xfce4-terminal -e "bash -c '$cmd; echo; read -p \"Press Enter to close...\"'";;
        mate-terminal)
            mate-terminal -- bash -c "$cmd; echo; read -p 'Press Enter to close...'";;
        tilix)
            tilix -e "bash -c '$cmd; echo; read -p \"Press Enter to close...\"'";;
        alacritty)
            alacritty -e bash -c "$cmd; echo; read -p 'Press Enter to close...'";;
        x-terminal-emulator)
            x-terminal-emulator -e bash -c "$cmd; echo; read -p 'Press Enter to close...'";;
    esac
}

# Add 'true' At The End Of Menu Prompt To Make Script Automatically Run With Sudo. Example: 1) launchTerminal "$CMD1" true;;

menu() {
    while true; do
        banner
        echo "${CYAN} [1] ${GREEN} TOMCAT C2 SERVER ${RESET}"
        echo "${CYAN} [2] ${GREEN} TOMCAT C2 SERVER [FLASK] ${RESET}"
        echo "${CYAN} [3] ${GREEN} TOMCAT C2 AGENT ${RESET}"
        echo "${CYAN} [4] ${GREEN} TOMCAT C2 AGENT [Minimal] ${RESET}"
        echo "${CYAN} [0] ${GREEN} Exit ${RESET}"
        echo
        read -rp "${RED}[+] ${YELLOW} Select >>> : ${CYAN}" choice
        case "$choice" in
        1) launchTerminal "$CMD1" ;;
        2) launchTerminal "$CMD2" ;;
        3) launchTerminal "$CMD3" ;;
        4) launchTerminal "$CMD4" ;;
        0) echo "${YELLOW} [E] ${GREEN} Exiting. ${RESET}"; exit 0 ;;
        *) echo "${RED} [!] ${YELLOW} Invalid Options! ${RESET}"; sleep 1 ;;
        esac
    done
}

menu
