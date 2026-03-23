#define MyAppName "video_bd"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "xgzit"
#define MyAppURL "https://github.com/xgzit/video_bd"
#define MyAppExeName "video_bd.exe"
#define MyAppDescription "全网视频批量下载工具"

[Setup]
AppId={{F3A7B2C1-D4E5-4F6A-9B8C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppComments={#MyAppDescription}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=release
OutputBaseFilename=video_bd_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=resources\icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 版权信息
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDescription}
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}

; 安装时请求管理员权限，支持用户自由选择安装目录（含 D 盘等）
PrivilegesRequired=admin

; 安装前自动关闭正在运行的旧版本，避免文件被占用
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

; 安装后不需要重启
RestartIfNeededByRun=no

[Languages]
Name: "chinesesimp"; MessagesFile: "resources\ChineseSimplified.isl"

[Tasks]
; 桌面快捷方式：默认勾选
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

; 升级时清理旧版 _internal 目录，防止删除的文件残留
[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\build\video_bd\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\build\video_bd\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}"; Permissions: everyone-full

[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"; Tasks: desktopicon

[Run]
; 安装完成后提供"立即启动"选项
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent runascurrentuser
