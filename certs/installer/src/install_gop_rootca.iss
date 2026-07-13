; ============================================================================
;  GOP rootCA Installer - Inno Setup Script
;  Target  : Windows 10 / 11 (x64) - 폐쇄망 클라이언트 PC
;  Purpose : mkcert 로 발급한 rootCA.pem 을 LocalMachine\\Root 에 등록
;  Author  : GOP API Server Team
;  Version : 1.0.0
; ============================================================================

#define MyAppName        "GOP rootCA Installer"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "GOP API Server Team"
#define MyAppURL         "https://gop.local/"
#define MyAppExeNameOut  "GOP-RootCA-Installer-v1.0.0.exe"
#define SrcDir           "..\\"
#define PayloadDir       SrcDir + "payload"
#define BuildDir         SrcDir + "build"

[Setup]
AppId={{F2A3B7C1-9D40-4E2B-A7C5-1E8F4A92B3DA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=GOP rootCA Trust Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; ---- 설치 위치 ----
DefaultDirName={autopf}\\GOP\\RootCAInstaller
DefaultGroupName=GOP
DisableProgramGroupPage=yes
DisableDirPage=auto
CreateAppDir=yes
Uninstallable=yes
UninstallDisplayName=GOP rootCA (신뢰할 수 있는 루트 인증서)
UninstallDisplayIcon={app}\\rootCA.pem

; ---- UAC: 관리자 권한 필수 (LocalMachine\\Root 쓰기) ----
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=

; ---- 빌드 출력 ----
OutputDir={#BuildDir}
OutputBaseFilename=GOP-RootCA-Installer-v{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
LZMAUseSeparateProcess=yes

; ---- 아키텍처 ----
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763

; ---- UI ----
WizardStyle=modern
ShowLanguageDialog=no
DisableWelcomePage=no
DisableReadyPage=no
DisableFinishedPage=no
LicenseFile={#SrcDir}src\\LICENSE_KO.txt
SetupLogging=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\\Korean.isl"

[CustomMessages]
korean.RegisteringCert=GOP 루트 인증서를 신뢰할 수 있는 루트 인증 기관 저장소에 등록 중입니다...
korean.RemovingCert=GOP 루트 인증서를 신뢰 저장소에서 제거 중입니다...

[Files]
; rootCA.pem 임베드 + 보조 PS1 임베드
Source: "{#PayloadDir}\\rootCA.pem"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SrcDir}src\\post_install.ps1";  DestDir: "{app}"; Flags: ignoreversion
Source: "{#SrcDir}src\\pre_uninstall.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; 설치 페이지 진행률 마지막 단계에서 호출
Filename: "{sys}\\WindowsPowerShell\\v1.0\\powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\\post_install.ps1"" -CertPath ""{app}\\rootCA.pem"""; \
    StatusMsg: "{cm:RegisteringCert}"; \
    Flags: runhidden waituntilterminated

[UninstallRun]
; 제어판 '제거' 클릭 시 호출
Filename: "{sys}\\WindowsPowerShell\\v1.0\\powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\\pre_uninstall.ps1"" -CertPath ""{app}\\rootCA.pem"""; \
    RunOnceId: "RemoveGopRootCA"; \
    Flags: runhidden waituntilterminated

[Code]
// ---------- 사전 점검 ----------
function InitializeSetup(): Boolean;
var
  WinVer: TWindowsVersion;
begin
  Result := True;
  GetWindowsVersionEx(WinVer);
  if WinVer.Major < 10 then
  begin
    MsgBox('이 인스톨러는 Windows 10/11 에서만 실행 가능합니다.', mbError, MB_OK);
    Result := False;
  end;
end;

// ---------- 설치 후 결과 검증 ----------
procedure CurStepChanged(CurStep: TSetupStep);
var
  LogPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    LogPath := ExpandConstant('{%TEMP}\\GOP-RootCA-Install.log');
    if not FileExists(LogPath) then
      MsgBox('인증서 등록 로그가 생성되지 않았습니다. %TEMP%\\GOP-RootCA-Install.log 를 확인하세요.',
             mbInformation, MB_OK);
  end;
end;
