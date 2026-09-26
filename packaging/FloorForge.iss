[Setup]
AppId={{69852C8A-BA3E-4FA8-B38B-94FDDEFE0578}
AppName=FloorForge
AppVersion=0.2.0-alpha
AppPublisher=FloorForge
DefaultDirName={localappdata}\Programs\FloorForge
DefaultGroupName=FloorForge
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=FloorForge-0.2.0-Setup-unsigned
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\FloorForge.exe
[Files]
Source: "..\dist\FloorForge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\FloorForge"; Filename: "{app}\FloorForge.exe"
Name: "{userdesktop}\FloorForge"; Filename: "{app}\FloorForge.exe"
[Run]
Filename: "{app}\FloorForge.exe"; Description: "Open FloorForge"; Flags: nowait postinstall skipifsilent
; Project files live in the user's .floorforge folder and are not removed here.
