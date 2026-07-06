# GOP API Server 자동 설치 문제 — 근본 원인 규명 및 해결 통지

- **작성일**: 2026-07-07
- **응답 대상**: 다른 PC 설치 팀 (`docs/prds/GOP_API_Server_자동설치_문제점_정리.md` 원문 작성 팀)
- **응답 세션**: `pids-api-server` 서버 세션
- **커밋/태그**: `release/v6.0` 위 → `v6.0-installer_ps2exe_path_fix`
- **원 문서**: `docs/prds/GOP_API_Server_자동설치_문제점_정리.md`

---

## 📌 두괄식 결론

| 항목 | 결과 |
|---|---|
| 원 문서 진단 (winget PATH 미반영) | ⚠️ **부분 오진** — 현재 코드는 winget 을 쓰지 않음 (GitHub 직접 다운로드) |
| **진짜 근본 원인** | ✅ **규명** — PS2EXE 로 빌드된 EXE 에서 `$PSScriptRoot` · `$MyInvocation.MyCommand.Path` · `$PSCommandPath` 가 **전부 빈 문자열** → `CertDir` 이 빈 값 → 인증서가 엉뚱한 곳(또는 실패) |
| 실측 증거 | ✅ probe EXE 로 6개 경로 변수 동작 실측 (아래 §3) |
| 왜 개발 PC 엔 무문제였나 | ✅ 규명 — 개발 PC 엔 인증서/mkcert 가 이미 있어 문제 코드 경로를 **한 번도 안 탐** (아래 §5) |
| 수정 | ✅ 완료 (3층: 경로획득 + bootstrap 명시전달 + 안전망) + EXE 재빌드 |
| 검증 | ✅ 재빌드된 EXE 를 신규 PC 조건으로 실행 → CertDir 정확 (아래 §6) |
| 재발 방지 | ✅ §7 |

**한 줄 요약**: winget 문제가 아니라 **PS2EXE 환경에서 스크립트 경로 변수가 모두 빈 문자열**이 되어 인증서 출력 경로가 깨진 것. `MainModule.FileName` 으로 EXE 절대경로를 획득하도록 고쳤고, EXE 를 신규 PC 조건에서 실행해 경로가 정확함을 실측 확인했습니다.

---

## 1. 원 문서 진단 vs 실제 코드

원 문서는 6개 문제를 지적했습니다. 현재 코드(`v6.0-cert_installer_fix` 반영본) 기준 대조:

| 원문 문제 | 현재 코드 실제 | 판정 |
|---|---|---|
| 1. winget 설치 직후 PATH 미반영 | 현재 코드는 **winget 미사용**. `Install-Mkcert` 가 GitHub Release 에서 `Invoke-WebRequest` 로 직접 다운로드 후 **절대경로**로 실행 | ⚠️ 옛 EXE 기준 추정 — 현재 무관 |
| 2. bootstrap 이 인증서 로직을 EXE 에 위임 | 사실. 다만 위임 자체가 문제는 아님 → **위임 시 -CertDir 명시 전달**로 강화 (이번 수정) | ✅ 보강 |
| 3. `certs\certs` 중첩 가능성 | **정확한 방향** — 단 원인은 `Join-Path $PSScriptRoot 'certs'` 가 아니라 **PS2EXE 에서 $PSScriptRoot 자체가 빈 문자열**인 것 | ✅ 근본 규명 |
| 4. mkcert 명령 이름 호출 | 현재 코드는 이미 **절대경로 실행** (`Invoke-Mkcert -ExePath $mkcert` → `Start-Process -FilePath`) | ⚠️ 이미 해결됨 |
| 11.1 EXE 파라미터 수신 | `param($CertDir)` 존재 → PS2EXE 가 param 지원 → 수신 가능 | ✅ 확인 |
| 11.2 EXE 재빌드 필요 | 사실 — 이번 수정 후 **재빌드 완료** | ✅ |

**즉 원 문서는 증상(경로 불일치)과 방향(3번)은 맞혔으나, 원인을 winget/PATH 로 오지목**했습니다. 실제 원인은 그 아래층인 **PS2EXE 경로 변수 소실**입니다. 정확한 실측으로 규명했으니 아래를 봐주세요.

---

## 2. 진짜 근본 원인 — PS2EXE 경로 변수 소실

`server_install.ps1` 의 (수정 전) 경로 획득:

```powershell
$script:ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot }
                     else { Split-Path -Parent $MyInvocation.MyCommand.Path }
```

- **PS1 직접 실행**(개발 PC): `$PSScriptRoot` 정상 → OK
- **PS2EXE 빌드된 EXE 실행**(신규 PC): `$PSScriptRoot` = **빈 문자열** → else 분기 → `$MyInvocation.MyCommand.Path` 도 **빈 문자열** → `Split-Path -Parent ''` = **빈 문자열/에러**
  → `$script:ScriptRoot = ''`
  → `CertDir` 판정에서 `'' -like '*installer_ps2exe*'` = false → `$CertDir = ''`
  → `$crt = Join-Path '' 'server.crt'` → **에러 또는 상대경로 `server.crt`** (CWD 에 생성)
  → bootstrap 은 `certs\server.crt` 를 검사 → **불일치 → "인증서 없음" 실패**

이게 사용자가 겪은 정확한 증상입니다.

---

## 3. 실측 증거 (probe EXE)

PS2EXE 로 빌드한 probe EXE 를 실행해 6개 경로 변수를 실측했습니다 (2026-07-07):

| 변수 | PS2EXE EXE 실행 시 값 |
|---|---|
| `$PSScriptRoot` | **`` (빈 문자열)** |
| `$MyInvocation.MyCommand.Path` | **`` (빈 문자열)** |
| `$PSCommandPath` | **`` (빈 문자열)** |
| `$MyInvocation.MyCommand.Definition` | (스크립트 소스코드 전체 — 경로 아님) |
| `$PWD.Path` | 실행 CWD (예: `C:\Users\gh`) |
| **`[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName`** | **`...\xxx.exe` (EXE 절대경로)** ← 유일하게 신뢰 가능 |

**결론**: PS2EXE EXE 에서 스크립트 위치를 얻는 유일한 방법은 `MainModule.FileName` 입니다.

---

## 4. 수정 (3층 방어)

### L1. `server_install.ps1` — PS2EXE-safe 경로 획득

```powershell
$script:ScriptRoot =
    if ($PSScriptRoot) { $PSScriptRoot }                       # PS1 직접 실행
    elseif ($MyInvocation.MyCommand.Path) {
        Split-Path -Parent $MyInvocation.MyCommand.Path
    } else {
        # PS2EXE EXE: MainModule.FileName 만 EXE 절대경로를 준다
        try { Split-Path -Parent ([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName) }
        catch { (Get-Location).Path }                          # 최후 안전망
    }
```
추가로 `CertDir` 이 그래도 빈 값이면 CWD 로 폴백하는 방어 코드.

### L2. `server_install.ps1` — `-NonInteractive` 스위치

기존엔 EXE 가 중간에 **"추가 SAN 입력"** `Read-Host` 와 종료 시 **"엔터를 눌러 종료"** `Read-Host` 에서 멈춰 자동화가 정지했습니다. `-NonInteractive` 지정 시 두 프롬프트를 모두 스킵.

### L3. `bootstrap.ps1` — `-CertDir` 명시 전달 + 안전망

```powershell
$installArgs = @('-CertDir', "`"$certDir`"", '-NonInteractive')
Start-Process -FilePath $serverInstallExe -ArgumentList $installArgs -WorkingDirectory $certDir -Wait -PassThru
```
- **-CertDir 명시** → EXE 내부 경로 자동판정에 **의존하지 않음** (L1 이 실패해도 안전)
- **-NonInteractive** → EXE 무인 진행
- **-WorkingDirectory** → 상대경로 폴백 대비
- 발급 후 `certs\server.crt` 가 없으면 `repoRoot` 하위를 **재귀 탐색**해 발견 위치에서 `certs\` 로 회수 (certs\certs 중첩 등 어떤 오생성도 흡수)

### L4 (부수). `.gitignore` — mkcert.exe 커밋 방지

신규 PC 에서 `certs\mkcert.exe` 가 자동 다운로드되므로 (~5MB) 실수 커밋 방지 규칙 추가.

---

## 5. 왜 개발 PC 에서는 문제가 없었나 (핵심 질문)

세 가지가 겹쳐 **문제 코드 경로를 한 번도 안 탔기 때문**입니다:

1. **개발 PC 엔 `certs\server.crt` · `server.key` 가 이미 존재** → `bootstrap.ps1` 이 "인증서 이미 있음 → 스킵" 분기를 타서 **`server_install.exe` 를 아예 실행하지 않음**. → PS2EXE 경로 버그가 발동할 기회 자체가 없음.
2. **개발 PC 엔 mkcert 가 PATH 에 이미 설치** → 설령 EXE 가 실행돼도 `Find-Mkcert` 가 PATH 에서 찾아 다운로드 경로를 안 탐.
3. **EXE 를 "신규 PC 조건(인증서 없음 + mkcert 없음)"에서 실제로 돌려본 적이 없음** → 우리는 EXE 를 `빌드`만 하고, bootstrap 실측도 "인증서 이미 있음 → 스킵" 경로만 확인 → PS2EXE 의 `$PSScriptRoot` 빈 문자열 동작을 EXE 로 실측하지 못함.

**한 문장**: "개발 PC 는 이미 다 갖춰져 있어 자동설치의 취약 경로를 밟지 않았고, 신규 PC 재현 테스트를 하지 않아 잠복했다."

---

## 6. 검증 (재빌드된 EXE, 신규 PC 조건 재현)

수정 스크립트로 EXE 재빌드 후, 경로 계산 로직을 EXE 로 실행해 실측 (2026-07-07):

| 시나리오 | ScriptRoot | CertDir | crt 출력 대상 |
|---|---|---|---|
| **A. 신규 PC 재현** (EXE 는 `certs\`, CWD=`USERPROFILE`) | `...\certs` ✅ | `...\certs` ✅ | `...\certs\server.crt` ✅ |
| **B. `-CertDir` 명시** (bootstrap 방식) | `...\certs` ✅ | `...\certs` ✅ | `...\certs\server.crt` ✅ |

**수정 전이었다면** 시나리오 A 에서 ScriptRoot=`''` → CertDir=`''` → `server.crt`(CWD 상대경로) → bootstrap 검사 경로와 불일치 → 실패. **수정 후 두 시나리오 모두 bootstrap 이 검사하는 정확한 경로**를 반환.

---

## 7. 재발 방지

1. **PS2EXE 로 빌드하는 모든 스크립트는 경로를 `MainModule.FileName` 으로 획득** — `$PSScriptRoot`/`$MyInvocation`/`$PSCommandPath` 는 EXE 에서 신뢰 불가. (server_install / client_install / build 스크립트 공통 원칙)
2. **인증서 경로는 호출측(bootstrap)이 `-CertDir` 로 명시 전달** — 피호출 EXE 의 경로 자동판정에 의존하지 않음.
3. **PS2EXE EXE 는 항상 `-NonInteractive` 로 무인 실행 가능해야** — 자동화 흐름이 `Read-Host` 에서 멈추지 않도록.
4. **"신규 PC 시나리오"(인증서 없음 + mkcert 없음 + PS2EXE 경로)를 릴리스 전 재현 검증** — 개발 PC 는 이미 갖춰져 있어 취약 경로를 안 밟으므로, 별도 clean 환경 재현이 필수. (본 이슈로 절감)
5. **스크립트 수정 후 반드시 EXE 재빌드** — PS2EXE 는 빌드 시점 코드를 embed. (원 문서 11.2 와 동일 인식)

---

## 8. 다른 PC 즉시 적용

```powershell
# 1) 최신 코드 pull
git pull origin release/v6.0

# 2) (이미 새 EXE 가 커밋돼 있으므로 바로 실행 가능)
#    최소 조치: bootstrap.ps1 실행
powershell -ExecutionPolicy Bypass -File bootstrap.ps1

#    또는 완전 무인:
powershell -ExecutionPolicy Bypass -File bootstrap.ps1 -NonInteractive
```

폐쇄망(인터넷 차단)이면 `certs\mkcert.exe` 를 미리 동봉하면 자동 다운로드를 건너뜁니다.

---

## 9. 참조

- **원 문서**: `docs/prds/GOP_API_Server_자동설치_문제점_정리.md`
- **서버 커밋**: 태그 `v6.0-installer_ps2exe_path_fix` (release/v6.0 위)
- **CHANGELOG**: `CHANGELOG.md` → v6.0-installer_ps2exe_path_fix 섹션
- **파일**: `certs/installer_ps2exe/server_install.ps1` (L1·L2), `bootstrap.ps1` (L3), `.gitignore` (L4), 재빌드된 `certs/server_install.exe`·`certs/client_install.exe`
- **저장소**: origin=`github.com/lsirikh/GopApiServer`, gitea=`192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server`
