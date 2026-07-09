<!-- auto-section-start -->
# 프로젝트 문서 인덱스

- **마지막 갱신**: 2026-07-03 (v6.0 최종 반영)
- **현재 릴리스**: v6.0 (Async 대전환 완결, tag `v6.0`, commit `61e46fe`)
- **활성 브랜치**: `release/v6.0` (tip) · `release/v5.4` (안전점) · `main`

---

## Master Specs — 마스터 명세

프로젝트 최상위 계약/명세 문서. 5중 싱크(코드·Swagger·명세서·Docker Image·Container) 준수 대상.

| 파일 | 역할 | 위치 |
|------|------|------|
| [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) | GOP REST API 마스터 명세 (git 추적본) | repo root |
| [CHANGELOG.md](../CHANGELOG.md) | 릴리스 변경 이력 (v6.0 완결 반영) | repo root |
| [README.md](../README.md) | 프로젝트 개요 | repo root |
| [CONTRACT_GOP_Server_v5.2.md](prds/CONTRACT_GOP_Server_v5.2.md) | v5.2 계약 스냅샷 (권한/스케쥴링) | docs/prds |
| [ADR_Permission_Model_v5.2.md](prds/ADR_Permission_Model_v5.2.md) | 권한 모델 결정 기록 (R9 중앙집행 / R10 권한모델) | docs/prds |

---

## PRDs — 요구사항 정의서 (docs/prds/)

| 파일 | 내용 | 상태 | 날짜 |
|------|------|------|------|
| [PRD_Permission_Group_Scheduling.md](prds/PRD_Permission_Group_Scheduling.md) | 권한 그룹 스케쥴링 (FR-01~07) | Approved | 2026-06-30 |
| [PRD_Role_Simplification.md](prds/PRD_Role_Simplification.md) | Role 단순화 Phase 2 | Approved | 2026-07-02 |
| [PRD_Legacy_User_Removal.md](prds/PRD_Legacy_User_Removal.md) | v5.3 Legacy User 제거 | Approved | 2026-07-02 |
| [PRD_GOP_Server_Force_Logout.md](prds/PRD_GOP_Server_Force_Logout.md) | 강제 로그아웃 (sid 클레임 / per-session NATS / HMAC) | Draft | 2026-06-29 |
| [PRD_GOP_Server_Session_Settings.md](prds/PRD_GOP_Server_Session_Settings.md) | 세션 설정 계약 | Draft | 2026-06-29 |
| [PRD_GOP_Server_RBAC_Enforcement.md](prds/PRD_GOP_Server_RBAC_Enforcement.md) | RBAC 강제 (~99 endpoint 매트릭스) | Draft | 2026-06-29 |
| [account-session-authority-prd.md](prds/account-session-authority-prd.md) | 세션 권위 모델 통합 (ACC-P0-02/03/04 + 공통 revoke) | Draft | 2026-07-09 |

---

## Plans — 구현 플랜 (docs/plans/)

| 파일 | 연관 PRD | 진행률 | 날짜 |
|------|---------|--------|------|
| [Permission_Group_Scheduling-prd-plan.md](plans/Permission_Group_Scheduling-prd-plan.md) | [PRD](prds/PRD_Permission_Group_Scheduling.md) | 진행 중 | 2026-06-30 |
| [RBAC_Enforcement-prd-plan.md](plans/RBAC_Enforcement-prd-plan.md) | [PRD](prds/PRD_GOP_Server_RBAC_Enforcement.md) | v6.0에서 확대 완료 | 2026-06-30 |
| [Role_Simplification-prd-plan.md](plans/Role_Simplification-prd-plan.md) | [PRD](prds/PRD_Role_Simplification.md) | 완료 | 2026-07-02 |
| [Legacy_User_Removal-prd-plan.md](plans/Legacy_User_Removal-prd-plan.md) | [PRD](prds/PRD_Legacy_User_Removal.md) | 완료 | 2026-07-02 |

---

## Requests — 클라이언트/서버간 요청서

| 파일 | 내용 | 날짜 |
|------|------|------|
| [REQ_Server_Grants_ListAll.md](REQ_Server_Grants_ListAll.md) | Grants ListAll endpoint 요청 | 2026 |
| [REQ_Server_Session_Cleanup.md](REQ_Server_Session_Cleanup.md) | 세션 정리 요청 | 2026 |
| [REQUEST_Reports_Verb_RBAC_Enforcement.md](REQUEST_Reports_Verb_RBAC_Enforcement.md) | Reports 동사 기반 RBAC 강제 요청 (v5.4 반영) | 2026-07-03 |
| [GOP_Server_API_v5.3_Legacy_User_Removal_NOTIFY.md](GOP_Server_API_v5.3_Legacy_User_Removal_NOTIFY.md) | v5.3 Legacy User 제거 통지 | 2026-07-02 |
| [GOP_Server_API_v5.3_Phase2_Role_Simplification_NOTIFY.md](GOP_Server_API_v5.3_Phase2_Role_Simplification_NOTIFY.md) | v5.3 Phase 2 Role Simplification 통지 | 2026-07-02 |
| [GOP_Server_API_FollowupRequests.md](GOP_Server_API_FollowupRequests.md) | 후속 요청 집합 | 2026-06 |
| [GOP_Server_API_OpenQuestions.md](GOP_Server_API_OpenQuestions.md) | Open Questions 리스트 | 2026-06 |
| [GOP_Server_API_OpenQuestions_RESPONSE.md](GOP_Server_API_OpenQuestions_RESPONSE.md) | Open Questions 응답 | 2026-06 |
| [GOP_Server_API_v4.9_Review_Issues.md](GOP_Server_API_v4.9_Review_Issues.md) | v4.9 리뷰 이슈 | 2026-06 |
| [GOP_Server_API_v4.9_Review_RESPONSE.md](GOP_Server_API_v4.9_Review_RESPONSE.md) | v4.9 리뷰 응답 | 2026-06 |

---

## Operations Guides — 운영 가이드

| 파일 | 대상 | 날짜 |
|------|------|------|
| [DOCKER_MAINTENANCE.md](DOCKER_MAINTENANCE.md) | Docker 유지보수 (autoheal, 로그 회전) | 2026-07-03 |
| [API_LOGS_PARTITION_MAINTENANCE.md](API_LOGS_PARTITION_MAINTENANCE.md) | api_logs 파티셔닝 유지보수 (v6.0 도입) | 2026-07-03 |
| [GOP_ForceLogout_Activation_Guide.md](GOP_ForceLogout_Activation_Guide.md) | 강제 로그아웃 활성화 절차 | 2026-07-03 |
| [GUIDE_Grant_Scheduling_Client_v5.2.md](prds/GUIDE_Grant_Scheduling_Client_v5.2.md) | 클라이언트용 Grant 스케쥴링 가이드 | 2026-06-30 |
| [GUIDE_RBAC_Activation_v5.2.md](prds/GUIDE_RBAC_Activation_v5.2.md) | RBAC 활성화 가이드 | 2026-06-30 |
| [GOP_RootCA_Installer_Guide.md](GOP_RootCA_Installer_Guide.md) | mkcert + Inno Setup rootCA 인스톨러 (HTTPS 정책) | 2026-06-25 |
| [DB_Admin_Usage_Guide.md](DB_Admin_Usage_Guide.md) | DB 관리 가이드 | 2025-11 |
| [Docker_Commands.md](Docker_Commands.md) | Docker 명령어 참조 | 2025-11 |

---

## Reports — 분석/현황 문서

| 파일 | 내용 | 날짜 |
|------|------|------|
| [GOPDB_통합_원인분석_및_조치_20260702.md](prds/GOPDB_통합_원인분석_및_조치_20260702.md) | GOPDB 통합 문제 A 원인분석 및 조치 (A-7 6/6 완결 근거) | 2026-07-02 |
| [Report_System_Development_Status.md](Report_System_Development_Status.md) | 리포트 시스템 개발 현황 | 2026 |
| [Report_구현현황_분석.md](Report_구현현황_분석.md) | 리포트 구현 현황 분석 | 2026 |
| [PROGRESS_SUMMARY.md](PROGRESS_SUMMARY.md) | 전체 진척 요약 | 2026 |
| [PROJECT_SCHEDULE_v4.3_납품계획.md](PROJECT_SCHEDULE_v4.3_납품계획.md) | v4.3 납품 계획 | 2026 |
| [PROJECT_SCHEDULE_잔여핵심작업_상세.md](PROJECT_SCHEDULE_잔여핵심작업_상세.md) | 잔여 핵심 작업 상세 | 2026 |
| [WorkLog_Recent5Days.md](WorkLog_Recent5Days.md) | 최근 5일 작업 로그 | 2026 |
| [UI개발진척도.md](UI개발진척도.md) | UI 개발 진척도 | 2026 |
| [통합상황도_개발_검증_일정.md](통합상황도_개발_검증_일정.md) | 통합상황도 개발/검증 일정 | 2026 |

---

## Memory — 세션 상태 (docs/memory/)

| 파일 | 역할 |
|------|------|
| [session-context.md](memory/session-context.md) | 현재 세션 컨텍스트 (다음 실행 기점) |
| [pipeline-state.json](memory/pipeline-state.json) | 기계적 파이프라인 상태 (Track/Phase) |
| [SESSION_COORDINATION.md](memory/SESSION_COORDINATION.md) | 세션 코디네이션 규약 |
| [feedback-rules.json](memory/feedback-rules.json) | 피드백 규칙 (learn 스킬 산출) |
| [instincts.jsonl](memory/instincts.jsonl) | 추출된 instinct 로그 |
| [audit-log.jsonl](memory/audit-log.jsonl) | 감사 로그 |

---

## Legacy Specs & Design — 과거 명세/설계 (참고용)

| 파일 | 내용 |
|------|------|
| [API_Documentation.md](API_Documentation.md) | v4 이전 API 문서 (구버전) |
| [Server_API_Schema_Reference.md](Server_API_Schema_Reference.md) | 서버 API 스키마 참조 |
| [GOP_Device_Refactoring_스키마.md](GOP_Device_Refactoring_스키마.md) | Device 리팩토링 스키마 |
| [GOP_스키마_전체.md](GOP_스키마_전체.md) | GOP 전체 스키마 |
| [GOP_통제시스템_UI_연동설계.md](GOP_통제시스템_UI_연동설계.md) | 통제 시스템 UI 연동 설계 |
| [GOP_통합상황도_스키마.md](GOP_통합상황도_스키마.md) | 통합상황도 스키마 |
| [Gop_Message_Broker_연동설계.md](Gop_Message_Broker_연동설계.md) | NATS 메시지 브로커 연동 설계 |
| [GOP_MainControl_UI.md](GOP_MainControl_UI.md) | Main Control UI 설계 |
| [FIGMA_Report_System_Design.md](FIGMA_Report_System_Design.md) | 리포트 시스템 Figma 디자인 |
| [FIGMA_Lamp_Page_Guide.md](FIGMA_Lamp_Page_Guide.md) | Lamp 페이지 Figma 가이드 |
| [SMCS_SCREEN_DESIGN_GUIDE.md](SMCS_SCREEN_DESIGN_GUIDE.md) | SMCS 화면 디자인 가이드 |
| [SMCS_Account_Pages_Design.md](SMCS_Account_Pages_Design.md) | SMCS 계정 페이지 디자인 |
| [AUDIT_LOG_SCREEN_DESIGN.md](AUDIT_LOG_SCREEN_DESIGN.md) | 감사 로그 화면 디자인 |
| [SCREEN_CONFIG_CHANGE_LOG.md](SCREEN_CONFIG_CHANGE_LOG.md) | 화면 설정 변경 로그 |
| [CLAUDE_TDD_GUIDE.backup.md](CLAUDE_TDD_GUIDE.backup.md) | TDD/Tidy First 원본 가이드 |
| [Manual.md](Manual.md) | 하네스 시스템 매뉴얼 |

> 그 외 v4.x 이하 다수의 PRD/Plan 파일(Action/Camera/Device/Event 계열)은 이 인덱스에서 명시적으로 나열하지 않으며 `docs/` 아래에 그대로 보존된다. 필요 시 파일명 기준 검색.

<!-- auto-section-end -->
