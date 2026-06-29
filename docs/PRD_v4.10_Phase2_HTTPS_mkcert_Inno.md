## §0 두괄식 (TL;DR)

**결론**: 폐쇄망 클라이언트 PC에 GOP API Server 의 mkcert 자체 서명 루트 인증서를 일관된 GUI 인스톨러로 등록하기 위해 **Inno Setup 6** 기반 단일 EXE 인스톨러 `GOP-RootCA-Installer-v1.0.0.exe` (≈1.8MB)를 채택·구현한다. 사용자는 USB → 더블클릭 → UAC "예" → 다음/다음/완료의 친숙한 흐름 3단계로 등록을 완료한다. 평가 점수 8.5점(A안)으로 PS2EXE(6.0점) 및 C# .NET Self-Contained(7.5점) 대비 우위.

**핵심 산출물**: `certs/installer/src/install_gop_rootca.iss` + `post_install.ps1` + `pre_uninstall.ps1` + `scripts/build.ps1`. 빌드 1회 명령으로 EXE 산출, USB 1회 복사로 배포 완료.

**범위**: 9중 정합(아래 §8) 통과, 차수 v4.9 Phase 분류 — Followup/배포 자동화. NATS/RBAC/DB 변경 없음. 서버 측 코드 변경 없음.

---

## §1 배경 + 결재

### 1.1 배경

- GOP 통제 시스템은 폐쇄망에서 mkcert 로 발급한 자체 서명 rootCA 를 사용해 HTTPS 통신을 보호한다.
- 그동안 클라이언트 PC에 신뢰 등록을 위해 매 PC 수동으로 `certutil -addstore -f Root rootCA.pem` 를 PowerShell 관리자 콘솔에서 입력하던 비표준 절차를 사용했다.
- 차장님 피드백: "사용자가 헷갈리지 않게 '다음/다음/완료' 패턴의 정식 인스톨러로 가자."
- 6대 컴포넌트(C1~C6) 중 C2(통제UI), C3(Central UI Web), C6(.NET 통합 클라이언트) 의 클라 PC 설치 단계에서 공통 사용한다.

### 1.2 결재 결과

| 항목 | 결정 |
|------|------|
| 채택 옵션 | **A. Inno Setup** |
| 우선순위 | v4.9 Followup, Phase 5 (배포 자동화 묶음) |
| 빌드 PC | 본사 보안 1구역 빌드 워크스테이션 1대 (Inno Setup 6 사전 설치) |
| 배포 매체 | USB 1매당 EXE + SHA256.txt |
| 검증 책임 | C3 통제 UI 팀 (V1~V7 체크리스트 필수) |

### 1.3 비범위

- 코드 서명서(EV/OV) 발급은 별도 차수 (PRD §7 권고만 기록).
- 차장님 Linux 클라(데모 제외) — 본 인스톨러는 Windows 10/11 전용.
- mkcert 자체 발급 절차는 외부 PRD `PRD_HTTPS_Cert_Issuance.md` 참조 (이 PRD는 발급된 rootCA.pem 가 있다는 가정).

---

## §2 옵션 비교 표 + 선정 사유

### 2.1 비교 매트릭스

| 평가축 | A. Inno Setup | B. PS2EXE | C. C# Self-Contained |
|--------|---------------|-----------|----------------------|
| 사용자 UX | 정식 GUI 인스톨러 ★★★★★ | 검은 콘솔 ★★ | 정식 GUI ★★★★★ |
| UAC 처리 | PrivilegesRequired=admin ★★★★★ | manifest 별도 작업 ★★★ | manifest 통합 ★★★★ |
| 빌드 복잡도 | 중간 (50줄 .iss) ★★★ | 낮음 (20줄 ps1) ★★★★★ | 높음 (5단계) ★★ |
| 파일 크기 | 1.5~2.5MB | 100~300KB | 70~100MB (.NET 임베드) |
| 백신 오탐 | 거의 없음 ★★★★★ | 잦음 (휴리스틱) ★★ | 거의 없음 ★★★★★ |
| 제거 자동화 | 제어판 자동 등록 ★★★★★ | 수동 ★ | 제어판 자동 가능 ★★★★ |
| 한국어 로케일 | 1줄 추가 ★★★★★ | 별도 인코딩 ★★★ | UI 직접 작성 ★★★★ |
| 팀 일관성 | 중립 ★★★ | 비일관 ★★ | .NET 팀과 일관 ★★★★ |
| **종합 점수** | **8.5 / 10** | 6.0 / 10 | 7.5 / 10 |

### 2.2 A안 선정 사유

1. 차장님 "다음/다음/완료" 패턴 요구사항을 자연스럽게 만족
2. 파일 크기 1.8MB → USB 1매에 다수 차수 EXE 동시 보관 가능 (C 안은 70MB+)
3. 백신 오탐 사례가 가장 적어 폐쇄망 EPP 정책과 마찰 최소
4. 한국어 로케일 `Languages\Korean.isl` 기본 동봉
5. 제어판 자동 등록 + 제거 스크립트 자동 실행으로 운영 부담 최소
6. .NET SDK 없는 빌드 PC에서도 빌드 가능 (Ironwall.Dotnet 빌드 환경과 분리)

### 2.3 B안(PS2EXE) 탈락 사유 핵심

- 검은 콘솔 UX는 차장님이 명시적으로 거부한 "임시변통" 인상
- V3/Defender 휴리스틱 오탐 발생 시 폐쇄망 전체 PC에 화이트리스트 배포 필요 → 운영 비용 ↑

### 2.4 C안(C# Self-Contained) 탈락 사유 핵심

- 단일 인증서 등록을 위해 70MB 임베드 .NET 런타임은 과대 (USB 비용)
- 빌드 단계 5단계 + WPF 학습 부담 → ROI 낮음
- 단, 향후 인스톨러가 "차수 자동 감지 + 서버 핑 + 진단 리포트 업로드" 등 풍부 기능을 갖게 되면 C안으로 재검토

---

## §3 구현 상세

### 3.1 디렉터리 구조

```
certs/installer/
├── src/
│   ├── install_gop_rootca.iss      # Inno Setup 메인
│   ├── post_install.ps1            # 등록 스크립트
│   ├── pre_uninstall.ps1           # 제거 스크립트
│   └── LICENSE_KO.txt              # 한국어 안내문
├── payload/
│   └── rootCA.pem                  # mkcert 발급본 (gitignore)
├── scripts/
│   ├── build.ps1                   # 빌드 진입점
│   └── verify.ps1                  # 산출물 검증
├── build/                          # 산출물 (gitignore)
│   ├── GOP-RootCA-Installer-v1.0.0.exe
│   └── SHA256.txt
├── README.md
└── .gitignore
```

### 3.2 핵심 동작 흐름 (시퀀스)

```
[사용자]                  [Setup.exe]                   [post_install.ps1]            [LocalMachine\Root]
    │   더블클릭            │                                │                              │
    │ ──────────────────► │ UAC 프롬프트                    │                              │
    │ ◄───── "예" ──────  │ (관리자 권한 획득)              │                              │
    │   Welcome → 다음    │ Inno UI 렌더링                  │                              │
    │   License → 동의    │ {app}에 rootCA.pem 임베드 해제 │                              │
    │   Install 클릭      │ [Run] 섹션 호출                │                              │
    │                     │ ──────────────────────────────► │ 1. PEM 파일 검증            │
    │                     │                                │ 2. Thumbprint 추출           │
    │                     │                                │ 3. ──── 중복 검사 ────────► │
    │                     │                                │ ◄────── 없음 ──────────────│
    │                     │                                │ 4. certutil -addstore Root  │
    │                     │                                │ ──────────────────────────► │
    │                     │                                │ ◄────── OK ────────────────│
    │                     │                                │ 5. 재조회 검증              │
    │                     │                                │ 6. %TEMP%\...log 기록       │
    │                     │ ◄────────── exit 0 ────────── │                              │
    │ ◄── 완료 화면       │ 제어판 등록 (Uninstall)         │                              │
    │   마침              │                                │                              │
```

### 3.3 install_gop_rootca.iss (요약 참조)

- `[Setup]` 섹션: AppId GUID 고정, `PrivilegesRequired=admin`, `OutputBaseFilename=GOP-RootCA-Installer-v1.0.0`, LZMA2 ultra 압축
- `[Languages]` 섹션: `MessagesFile: "compiler:Languages\Korean.isl"` 1줄로 한국어 전체 UI
- `[Files]` 섹션: payload\rootCA.pem 임베드, post_install.ps1/pre_uninstall.ps1 동봉
- `[Run]` 섹션: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File {app}\post_install.ps1 -CertPath {app}\rootCA.pem` (runhidden)
- `[UninstallRun]` 섹션: 동일 패턴으로 pre_uninstall.ps1 호출
- `[Code]` Pascal 섹션: InitializeSetup() 에서 Windows 10 미만 차단, CurStepChanged() 에서 로그 파일 존재 확인

상세 코드는 code_artifacts §0 (install_gop_rootca.iss) 참조.

### 3.4 post_install.ps1 핵심 로직

1. `New-Object X509Certificate2; $cert.Import($CertPath)` 로 PEM 로드
2. `Thumbprint` 추출 후 `LocalMachine\Root` 저장소를 ReadOnly 로 열어 비교
3. 중복이면 `exit 0` + 로그 `Result=ALREADY_INSTALLED`
4. `Start-Process certutil.exe -ArgumentList @('-addstore','-f','Root',$CertPath) -Wait -PassThru` 로 stdout/stderr 모두 캡쳐
5. ExitCode 비0이면 `throw` 로 ssPostInstall 단계에서 Inno가 에러 다이얼로그 표시
6. 재조회로 사후 검증 → `Result=SUCCESS` 기록
7. catch 블록에서 `Result=FAILED` 기록 후 `exit 1`

### 3.5 pre_uninstall.ps1 핵심 로직

- 동일하게 Thumbprint 식별 후 `$store.Open(ReadWrite); $store.Remove($cert)` 수행
- {app} 폴더가 이미 사라진 환경에서 호출되어도 `try/catch`로 graceful exit

### 3.6 build.ps1 자동화 흐름

```
[빌더] ─► build.ps1
            ├─ ISCC.exe 자동 탐색 (Program Files / Program Files (x86))
            ├─ payload\rootCA.pem PEM 헤더 검증
            ├─ build\ 디렉터리 생성
            ├─ Start-Process ISCC.exe install_gop_rootca.iss
            ├─ 산출 EXE 탐색 (가장 최근)
            ├─ SHA256 계산
            └─ SHA256.txt 작성 → 콘솔 출력
```

---

## §4 빌드 절차 (서버/빌드 PC)

### 4.1 1회 준비

```powershell
# (1) Inno Setup 6 설치
#     https://jrsoftware.org/isdl.php → innosetup-6.x.x.exe
#     기본 경로 'C:\Program Files (x86)\Inno Setup 6' 권장

# (2) 저장소 클론 또는 작업 트리 확인
cd c:\workspace_python\api-test-server\certs\installer
ls
```

### 4.2 차수마다 (rootCA 갱신 시)

```powershell
# (3) mkcert 발급본 복사
$CAROOT = (mkcert -CAROOT)
Copy-Item "$CAROOT\rootCA.pem" .\payload\rootCA.pem -Force

# (4) 빌드
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

# 출력 예:
#   [OK]  ISCC : C:\Program Files (x86)\Inno Setup 6\ISCC.exe
#   [OK]  PEM  : ...\payload\rootCA.pem  (2114 bytes)
#   [RUN] ISCC.exe "...\install_gop_rootca.iss"
#   ...
#   ===================================
#     Build SUCCESS
#   ===================================
#     파일   : ...\build\GOP-RootCA-Installer-v1.0.0.exe
#     크기   : 1,847,832 bytes
#     SHA256 : 7A3B2C... (64자)

# (5) 검증
.\scripts\verify.ps1 -ExePath .\build\GOP-RootCA-Installer-v1.0.0.exe
```

### 4.3 산출물

| 파일 | 위치 | 용도 |
|------|------|------|
| `GOP-RootCA-Installer-v1.0.0.exe` | `build/` | USB 배포 |
| `SHA256.txt` | `build/` | 무결성 검증 메모 |

---

## §5 배포 절차 (USB → 클라 PC)

### 5.1 빌드 PC → USB

1. USB의 `\GOP-RootCA\` 폴더 생성
2. `GOP-RootCA-Installer-v1.0.0.exe` + `SHA256.txt` 복사
3. (선택) `사용자_가이드.md` 또는 PDF 함께 복사
4. USB 안전 제거

### 5.2 클라 PC에서 실행

1. USB 삽입 (Autorun 차단 정책 정상)
2. 탐색기에서 `\GOP-RootCA\GOP-RootCA-Installer-v1.0.0.exe` 더블클릭
3. SmartScreen 경고 시 "추가 정보" → "실행"
4. UAC "예" 클릭
5. Inno 한국어 마법사: 환영 → 동의 → 설치 → 완료
6. (선택) PowerShell로 V1~V5 검증

### 5.3 배치 배포 (다수 PC)

- 그룹정책(GPO) 시작 스크립트로 EXE를 `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART` 인자로 호출 가능
- 예: `gpedit.msc → 컴퓨터 구성 → Windows 설정 → 스크립트 → 시작 → GOP-RootCA-Installer-v1.0.0.exe /VERYSILENT`
- SCCM/Intune 사용 시 동일 인자 가능

---

## §6 검증 + 트러블슈팅

### 6.1 검증 체크리스트 (V1~V7)

verification_steps 참조. 클라 PC 1대당 V1, V2, V4 는 필수, V3/V5/V6/V7 는 1차 배포 또는 장애 조사 시 수행.

### 6.2 트러블슈팅

troubleshooting 섹션의 7개 케이스 참조:
- SmartScreen 경고 (1)
- UAC 거부 (2)
- HTTPS 검증 실패 (3)
- certutil 실패 (4)
- 다중 버전 충돌 (5)
- 백신 격리 (6)
- 제거 잔존 (7)

---

## §7 보안

### 7.1 위협 모델

| 위협 | 영향 | 완화 |
|------|------|------|
| rootCA.pem 변조 (USB 이동 중) | 가짜 CA 등록 시 MITM 가능 | SHA256.txt 비교 필수, 보안팀 USB 전수 검사 |
| 인스톨러 EXE 변조 | 악성 행위 임베드 | SHA256.txt + (향후) 코드 서명 |
| 권한 상승 악용 | UAC 우회 | Inno PrivilegesRequired=admin 외 별도 우회 코드 없음 |
| 로그 노출 | %TEMP% 위치 PII 없음 | 인증서 메타정보만 기록 (개인정보 ×) |

### 7.2 코드 서명 권고

- 현재 v1.0.0은 코드 서명 미적용 (SmartScreen 1회 경고 발생)
- 권고: 사내 CA 또는 외부 OV/EV 코드 서명서 1매 발급 후 다음 명령으로 서명
  ```
  signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a GOP-RootCA-Installer-v1.0.0.exe
  ```
- EV 코드 서명서 적용 시 SmartScreen 경고 영구 제거 + 기업 백신 오탐 대폭 감소
- 별도 차수 (PRD_Code_Signing.md) 로 분리

### 7.3 보안팀 협업 항목

| 항목 | 책임 |
|------|------|
| USB 입출고 관리 | 보안1팀 |
| 빌드 PC 격리 운영 | 보안1팀 |
| EPP/EDR 화이트리스트 | 보안2팀 |
| 코드 서명서 발급 | IT기획 (v4.9 차차수) |

---

## §8 9중 정합 + 안전점 + 롤백

### 8.1 9중 정합 체크

| 축 | 본 PRD 영향 | 통과 |
|----|-------------|------|
| API v4.3 명세 | 영향 없음 (클라 PC 신뢰 등록) | OK |
| NATS v1.3 토픽 | 영향 없음 | OK |
| DB v2.7 스키마 | 영향 없음 | OK |
| RBAC 정책 | 영향 없음 | OK |
| Auth (JWT/jti) | 영향 없음 | OK |
| 감사 로그 | 인스톨러 자체 로그 별도, 서버 감사 영향 없음 | OK |
| .NET 통합 클라이언트 | rootCA 신뢰 후 HttpClient SSL 정상화 | 양성 영향 |
| Central UI Web | rootCA 신뢰 후 브라우저 경고 제거 | 양성 영향 |
| Static vs Runtime 시드 | 영향 없음 | OK |

### 8.2 안전점

- 빌드 PC에 mkcert 비밀키(rootCA-key.pem) 동봉 금지 — payload 에는 공개 인증서 .pem 만
- payload/rootCA.pem 은 .gitignore 로 추적 제외 (차수별 변동 + 보안 위생)
- post_install.ps1 의 `Start-Process -ArgumentList` 는 `$CertPath` 를 따옴표로 감싸 공백 경로 보호
- pre_uninstall.ps1 은 `$ErrorActionPreference=Continue` 로 부분 실패 허용 (제거 잔존 시 수동 대응 가능)

### 8.3 롤백 절차

1. 잘못된 인증서가 배포된 경우 (예: 손상된 PEM)
2. 보안팀이 USB 회수 + 신규 USB 배포 지시
3. 각 클라 PC: 제어판에서 구버전 제거 (U1) → 신규 EXE 재설치
4. 또는 도메인 관리자가 GPO로 `/VERYSILENT /UNINSTALL` 일괄 실행 후 신규 인스톨러 재배포

### 8.4 롤백 신호

- `%TEMP%\GOP-RootCA-Install.log` 에 `Result=FAILED` 가 N대 PC에서 동시 발생 → 즉시 배포 중단
- 클라 PC 다수에서 V4 (HTTPS 신뢰) 실패 보고 → SHA256 재검증

---

## §9 DoD (Definition of Done)

다음 11개 조건을 모두 만족하면 본 PRD 완료:

1. `certs/installer/src/install_gop_rootca.iss` 작성 완료 + 컴파일 무경고 통과
2. `post_install.ps1` / `pre_uninstall.ps1` 작성 완료 + 격리 VM 1회 dry-run 통과
3. `scripts/build.ps1` 작성 완료 + ISCC 자동 탐색 성공
4. `payload/rootCA.pem` 가 mkcert 발급본과 SHA256 일치
5. `build/GOP-RootCA-Installer-v1.0.0.exe` 산출 (1.5~2.5MB 범위)
6. `build/SHA256.txt` 생성 + 빌드 PC 콘솔 출력과 일치
7. 격리 VM에서 V1~V5 모두 PASS
8. 제어판에 "GOP rootCA Installer 1.0.0" 표시
9. 제거 후 V1 0행 출력 확인
10. `README.md` + `사용자_가이드.md` 작성 완료 + INDEX.md 갱신
11. session-context.md 갱신 + 차수 v4.9 Phase 5 완료 처리