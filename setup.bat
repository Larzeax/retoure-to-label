@echo off

REM Set paths
set currentPath=%cd%
set "pythonPath=python"
set "scriptPath=%currentPath%\pdf_processor.py"
set "batchFile=run_pdf_processor.bat"
set "regFile=setup_context_menu.reg"
set "venvPath=%currentPath%\venv"
set "sendToPath=%APPDATA%\Microsoft\Windows\SendTo"
set "shortcutName=!!Label Creator.lnk"


REM Replace backslashes with double backslashes for .reg file
set "escapedPythonPath=%pythonPath:\=\\%"
set "escapedScriptPath=%scriptPath:\=\\%"
set "escapedPath=%currentPath:\=\\%"
set "escapedVenvPath=%venvPath:\=\\%"

REM Create the virtual environment
if not exist "%venvPath%" (
    echo Creating a virtual environment...
    %pythonPath% -m venv "%venvPath%"
    echo Virtual environment created.
    echo Installing required packages...
    call "%venvPath%\Scripts\activate"
    pip install -r requirements.txt
    echo Required packages installed.
) else (
    echo Virtual environment already exists.
)

REM Create the batch file to run the Python script
(
    echo @echo off
    echo REM Navigate to the venv scripts folder
    echo cd /d "%venvPath%\Scripts"
    echo REM Activate the venv
    echo call activate
    echo REM Navigate back to the current directory
    echo cd /d %%~dp0
    echo REM Run the Python script with all selected files
    echo python "%scriptPath%" %%*
    echo pause
) > "%batchFile%"

echo Created %batchFile%.

REM Create a shortcut for the batch file in the SendTo folder
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%sendToPath%\\%shortcutName%'); $s.TargetPath = '%~dp0%batchFile%'; $s.Save()"

echo Created shortcut in the SendTo menu.

REM Create the .reg file for the context menu
(
    echo Windows Registry Editor Version 5.00
    echo.

    REM First registry key and value
    echo [HKEY_LOCAL_MACHINE\SOFTWARE\Classes\SystemFileAssociations\.pdf\shell\ProcessLabel]
    echo @="Process Label"

    REM Second registry key and value
    echo [HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Directory\shell\ProcessLabels]
    echo @="Process Labels"



    REM Second registry key and value
    echo [HKEY_LOCAL_MACHINE\SOFTWARE\Classes\SystemFileAssociations\.pdf\shell\ProcessLabel\command]
    echo @="\"%escapedPath%\\run_pdf_processor.bat\" \"%%1\""

    REM Second registry key and value
    echo [HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Directory\shell\ProcessLabels\command]
    echo @="\"%escapedPath%\\run_pdf_processor.bat\" \"%%1\""

) > "%regFile%"

echo Created %regFile%.

echo The setup is complete. Double-click %regFile% to add the context menu option.
pause
