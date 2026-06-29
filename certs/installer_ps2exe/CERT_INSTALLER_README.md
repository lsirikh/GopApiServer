# GOP 인증서 인스톨러 (Lite 2-EXE 패키지)

> 위치: `certs/CERT_INSTALLER_README.md`
> 차장님 결재: 클라/서버 단일 EXE 2개로 패키지화 -> `certs/` 폴더에 상시 배치

---

## TL;DR

| 산출물 | 실행 대상 | 역할 |
|---|---|---|
| `certs/server_install.exe` | API 서버 PC | mkcert 로컬 CA 등록 + `server.crt`/`server.key` 발급 |
| `certs/client_install.exe` | 클라이언트 PC | `rootCA.pem` 을 Windows 신뢰 저장소(Root) 등록 |

두 EXE 모두 더블클릭 -> UAC -> 한국어 콘솔 진행 -> 엔터 종료.

---

## Inno Setup 인스톨러(`certs/installer/`)와의 차이점

| 항목 | Inno Setup 인스톨러 | PS2EXE Lite 패키지 (본 산출물) |
|---|---|---|
| 위치 | `certs/installer/build/` | `certs/` 루트 |
| 형식 | 정식 Windows 인스톨러(설치/제거) | 단일 실행형 EXE |
| GUI | 마법사 형식 | 콘솔(한국어, 색상) |
| 빌드 도구 | Inno Setup Compiler | PowerShell + PS2EXE |
| 용량 | 수~수십 MB | 수백 KB |
| 용도 | 정식 출하용 | 현장 즉시 사용/임시 배포 |
| 유지 | 기존대로 유지 | 신규 추가 (병행) |

> Inno Setup 버전은 그대로 보존한다. 본 패키지는 "차장님 PC -> USB -> 현장 PC" 같은 가벼운 시나리오용이다.

---

## 사용 시나리오

### A. 신규 GOP 서버 1대 셋업

1. 서버 PC 에서 `certs/server_install.exe` 우클릭 -> 관리자 권한 실행
2. 추가 SAN(예: `192.168.0.50`) 입력
3. 발급 결과
   - `certs/server.crt`
   - `certs/server.key`
   - `certs/rootCA.pem`  (mkcert 의 CAROOT 에서 자동 복사)
4. Docker 재시작
   ```
   docker compose up -d --force-recreate api-server
   ```

### B. 클라 PC N대 셋업

1. 위에서 만들어진 `certs/client_install.exe` (rootCA 임베드 상태) 를 USB/파일공유로 배포
2. 각 클라 PC 에서 우클릭 -> 관리자 권한 실행
3. 자동으로 Windows `LocalMachine\Root` 저장소에 rootCA 등록
4. 브라우저/.NET 클라 재시작 -> HTTPS 경고 없이 접속

### C. 폐쇄망(인터넷 차단) 환경

- `server_install.exe` 와 같은 폴더에 `mkcert.exe` 를 미리 동봉
- 스크립트가 자동 다운로드를 건너뛰고 동봉 EXE 를 사용

---

## 로그 위치

| EXE | 로그 |
|---|---|
| server_install.exe | `%TEMP%\GOP-Server-Install.log` |
| client_install.exe | `%TEMP%\GOP-Client-Install.log` |

오류가 나면 위 로그를 먼저 확인한다.

---

## 빌드 (개발/PM 측)

```powershell
# 1) mkcert -CAROOT 에 rootCA.pem 이 있는 PC 에서
pwsh -ExecutionPolicy Bypass -File build_install_exe.ps1

# 결과
#   certs/server_install.exe
#   certs/client_install.exe
```

세부 옵션:

```powershell
build_install_exe.ps1 `
  -RootCaPath 'C:\Users\me\AppData\Local\mkcert\rootCA.pem' `
  -Version    '1.0.0.0' `
  -Company    'GOP' `
  -KeepTemp
```

---

## FAQ

**Q. mkcert 가 없는 PC 에서 server_install.exe 를 돌리면?**
A. 인터넷이 되면 GitHub Release 에서 자동 다운로드. 폐쇄망이면 같은 폴더에 `mkcert.exe` 동봉 필요.

**Q. client_install.exe 의 rootCA 가 바뀌면 재빌드해야 하나?**
A. 그렇다. rootCA 는 빌드 시점에 Base64 임베드된다. 갱신 시 `build_install_exe.ps1` 재실행.

**Q. EXE 가 SmartScreen 에 잡힌다.**
A. 코드사인 미적용 상태이기 때문이다. 정식 배포에는 Inno Setup + 코드사인 인스톨러를 쓰고, 본 EXE 는 사내/현장 한정으로 사용한다.

**Q. 이미 신뢰 저장소에 동일 rootCA 가 있으면?**
A. client_install.exe 는 Thumbprint 비교로 멱등 처리한다. 중복 등록 없음.

---

## 보안 메모

- 본 EXE 는 코드사인되어 있지 않다. 사내 망에서만 배포한다.
- `server.key` 는 절대 클라이언트 PC 로 전달하지 않는다. (server_install.exe 가 만든 `certs/` 그대로 두기만 하면 된다)
- `rootCA.pem` 임베드는 공개 인증서이므로 노출되어도 직접적인 키 유출은 아니다. 다만 동일 rootCA 로 발급된 임의 도메인의 서버를 신뢰하게 되므로 사내 한정 사용을 원칙으로 한다.
