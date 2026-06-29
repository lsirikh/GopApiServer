# GOP rootCA Installer (Inno Setup)

폐쇄망 클라이언트 PC에 GOP API Server 의 자체 서명 루트 인증서를
원클릭으로 등록하기 위한 Windows 인스톨러 (.exe).

## 빌드 절차 (빌드 PC, 1회 준비)

1. Inno Setup 6 설치 — https://jrsoftware.org/isdl.php
2. `mkcert -CAROOT` 경로의 `rootCA.pem` 을 `payload\rootCA.pem` 으로 복사
3. `powershell -ExecutionPolicy Bypass -File scripts\build.ps1`
4. `build\GOP-RootCA-Installer-v1.0.0.exe` 산출 + `SHA256.txt`

## 배포 절차 (USB → 클라 PC)

1. EXE + SHA256.txt 를 USB 에 복사
2. 클라 PC 에서 SHA256 비교
3. EXE 더블클릭 → UAC "예" → 다음 → 동의 → 설치 → 완료

## 검증

```powershell
Get-ChildItem Cert:\LocalMachine\Root | Where-Object Subject -Match 'mkcert|GOP'
```

## 제거

제어판 → 프로그램 추가/제거 → "GOP rootCA Installer" → 제거

상세 PRD: `docs/PRD_RootCA_Installer.md`
사용자 매뉴얼: `docs/GOP_rootCA_사용자_가이드.md`
