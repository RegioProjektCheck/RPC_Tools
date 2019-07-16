
  !include "MUI2.nsh"

;--------------------------------
;General

  RequestExecutionLevel user

  ;Name and file
  Name "Projekt-Check Profi"
  OutFile "projekt-check-profi-installer.exe"

  ;Default installation folder
  InstallDir "$DOCUMENTS\Projekt-Check Profi"

  ;Get installation folder from registry if available
  InstallDirRegKey HKLM "Software\ProjektCheck PROFI" ""

  ;Request application privileges for Windows Vista
  ;RequestExecutionLevel user

  !define MUI_ABORTWARNING
  !define MUI_FINISHPAGE_NOAUTOCLOSE

;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;Languages
  !insertmacro MUI_LANGUAGE "German"

;Files reserved
  ReserveFile "python27.dll"
  ;ReserveFile "rpc-installer.py"


  Function .onInit
	;Extract Install Options files
	;$PLUGINSDIR will automatically be removed when the installer closes
	InitPluginsDir

	File "/oname=$PLUGINSDIR\python27.dll" "python27.dll"
	;File "/oname=$PLUGINSDIR\rpc-installer.py" "rpc-installer.py"
  FunctionEnd

  Function .onGUIEnd
	nsPython::Finalize
  FunctionEnd

  Section "Projektcheck-Tools installieren"
    SetOutPath "$INSTDIR"
	;relative path
	File /r  /x *.exe /x .git /x .gitignore /x rpctools.egg-info /x *.pyc "..\..\*"
	;Store installation folder
	WriteRegStr HKLM "Software\ProjektCheck Profi" "" $INSTDIR

    CreateDirectory "$LOCALAPPDATA\Projekt-Check"
    FileOpen $4 "$LOCALAPPDATA\Projekt-Check\inst_dir.txt" w
    FileWrite $4 "$INSTDIR"
    FileClose $4

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
  SectionEnd

  Section "Bibliotheken installieren"

    nsPython::execFile "$INSTDIR\3 Programminterne Daten\installer\rpc-installer.py"
    Pop $0
    DetailPrint "Result: $0"
  SectionEnd

  Section "AddIn installieren"
	ExecShell "" "$INSTDIR\3 Programminterne Daten\addin\addin.esriaddin"
  SectionEnd

Section "Uninstall"

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\ProjektCheck Profi"

SectionEnd

