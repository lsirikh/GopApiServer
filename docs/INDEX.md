# docs/ Index

> 문서 단일 진입점. 141 파일을 9 카테고리로 정리.
> 최종 갱신: 2026-06-19 / 현재 차수: v4.6

---

## 🎯 가장 자주 찾는 것 (Top 5)

| # | 문서 | 용도 |
|---|---|---|
| 1 | [세션 컨텍스트](memory/session-context.md) | 현재 진행 상태 / 다음 세션 진입점 |
| 2 | [API 명세 v4.6](../GOP_Restful_Api_연동설계.md) | 전체 API 상세 (마스터) |
| 3 | [CHANGELOG](../CHANGELOG.md) | 모든 차수 변경 이력 |
| 4 | [README](../README.md) | 빠른 개요 + Docker 사용법 + 시드 명세 |
| 5 | [DB 스키마 v2.12](GOP_스키마_전체.md) | PostgreSQL 테이블 정의 |

---

## 📘 1. 명세서 (마스터)

| 문서 | 버전 |
|---|---|
| [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) | v4.6 (2026-06-19) |
| [GOP_스키마_전체.md](GOP_스키마_전체.md) | v2.12 (2026-06-19) |
| [Gop_Message_Broker_연동설계.md](Gop_Message_Broker_연동설계.md) | NATS 메시지 envelope |
| [GOP_통제시스템_UI_연동설계.md](GOP_통제시스템_UI_연동설계.md) | UI 연동 |
| [GOP_통합상황도_스키마.md](GOP_통합상황도_스키마.md) | 통합상황도 |

---

## 🛠 2. 현 차수 (v4.6) PRD + 가이드

| 문서 | 용도 |
|---|---|
| [PRD_v4.6_Critical_and_Preset.md](PRD_v4.6_Critical_and_Preset.md) | v4.6 종합 PRD (39KB) |
| [v46_camera_preset_restricted_zone_guide.md](v46_camera_preset_restricted_zone_guide.md) | Camera Preset 감시금지구역 매니저 가이드 |
| [v45_3way_critical_mismatches.html](v45_3way_critical_mismatches.html) | Critical 10건 HTML 시각화 |
| [PRD_v4.5_Debt_Cleanup.md](PRD_v4.5_Debt_Cleanup.md) | v4.5 부채 분석 |

---

## 📋 3. v4.x PRD 시리즈 (차수별)

### v4.4 (2026-06-18)
- [PRD_v4.4_Phase1_SpecSync.md](PRD_v4.4_Phase1_SpecSync.md) — Bulk API 명세 정정 14건
- [PRD_v4.4_Phase3_PostMortem.md](PRD_v4.4_Phase3_PostMortem.md) — Post-Mortem 보안 9건
- [PRD_v4.4_Phase4_Directional_JsonB.md](PRD_v4.4_Phase4_Directional_JsonB.md) — 지향성 + JSON→JSONB
- [v44_sync_guide.md](v44_sync_guide.md) — .NET 사본 동기화 가이드

---

## 📑 4. 도메인별 PRD (~85개)

### Device
- [PRD_Device_Structure_Refactoring.md](PRD_Device_Structure_Refactoring.md)
- [PRD_Device_Inheritance_Structure_Refactoring.md](PRD_Device_Inheritance_Structure_Refactoring.md)
- [PRD_Device_IsEnable_Field.md](PRD_Device_IsEnable_Field.md)
- [PRD_Device_Setting.md](PRD_Device_Setting.md) / [PRD_Device_Setting_PUT.md](PRD_Device_Setting_PUT.md)
- [PRD_Camera_Urls_JsonB.md](PRD_Camera_Urls_JsonB.md)
- [PRD_Camera_Preset_ROI.md](PRD_Camera_Preset_ROI.md)
- [PRD_CameraSetting_Tracking.md](PRD_CameraSetting_Tracking.md)
- [PRD_Lamp_Device.md](PRD_Lamp_Device.md)
- [PRD_Enclosure_Device.md](PRD_Enclosure_Device.md) / [PRD_Enclosure_Metrics_Separation.md](PRD_Enclosure_Metrics_Separation.md)
- [PRD_Controller_Sensor_Geolocation.md](PRD_Controller_Sensor_Geolocation.md)
- [PRD_DeviceGroup_Assign_Fix.md](PRD_DeviceGroup_Assign_Fix.md) / [PRD_DeviceGroup_BulkUnassign.md](PRD_DeviceGroup_BulkUnassign.md)
- [PRD_DeviceGroup_Support_Completion.md](PRD_DeviceGroup_Support_Completion.md)

### Event
- [PRD_Event_Structure_Refactoring.md](PRD_Event_Structure_Refactoring.md)
- [PRD_Event_ActionEvent_Refactoring.md](PRD_Event_ActionEvent_Refactoring.md)
- [PRD_ActionEvent_1N_Refactoring.md](PRD_ActionEvent_1N_Refactoring.md)
- [PRD_Event_Api_Refactoring.md](PRD_Event_Api_Refactoring.md)
- [PRD_Event_Device_Refactoring.md](PRD_Event_Device_Refactoring.md)
- [PRD_Event_Detail_JsonB.md](PRD_Event_Detail_JsonB.md)
- [PRD_Event_Field_Normalization.md](PRD_Event_Field_Normalization.md)
- [PRD_EventStatistics_Api.md](PRD_EventStatistics_Api.md)
- [PRD_DetectionLog_API.md](PRD_DetectionLog_API.md)
- [PRD_CategoryEvent_Refactoring.md](PRD_CategoryEvent_Refactoring.md)

### EventMapping (Bulk)
- [PRD_EventMapping_BulkOperations.md](PRD_EventMapping_BulkOperations.md)
- [PRD_EventMappingSpeaker.md](PRD_EventMappingSpeaker.md) / [PRD_EventMappingSpeaker_Revision.md](PRD_EventMappingSpeaker_Revision.md)
- [PRD_MappingSubResource_ListAPI.md](PRD_MappingSubResource_ListAPI.md)
- [PRD_CameraEventMapping_Cleanup.md](PRD_CameraEventMapping_Cleanup.md) / [PRD_CameraEventMapping_Refactoring.md](PRD_CameraEventMapping_Refactoring.md)

### Account / Auth / Security
- [PRD_Account_Design.md](PRD_Account_Design.md) / [PRD_Account_Implementation.md](PRD_Account_Implementation.md)
- [PRD_Auth_Migration.md](PRD_Auth_Migration.md)
- [PRD_Audit_Log.md](PRD_Audit_Log.md)
- [PRD_ConfigChangeLog.md](PRD_ConfigChangeLog.md)

### Server / System
- [PRD_NVR_Integration_Requirements.md](PRD_NVR_Integration_Requirements.md)
- [PRD_DB_Change_Monitor.md](PRD_DB_Change_Monitor.md) / [PRD_DB_Data_Manager.md](PRD_DB_Data_Manager.md)
- [PRD_PostgreSQL_Migration.md](PRD_PostgreSQL_Migration.md)
- [PRD_Malfunction_Device_Status.md](PRD_Malfunction_Device_Status.md)

### Report
- [PRD_Report_CustomTemplate_Filter.md](PRD_Report_CustomTemplate_Filter.md)
- [PRD_Report_PDF_Korean_Fix.md](PRD_Report_PDF_Korean_Fix.md)
- [PRD_Report_PDF_Preview.md](PRD_Report_PDF_Preview.md) / [PRD_Report_PDF_Pre*.md](.) (시리즈)

### API 정합 / 문서화
- [PRD_API_Gap_Analysis.md](PRD_API_Gap_Analysis.md)
- [PRD_API_Endpoint_Sync.md](PRD_API_Endpoint_Sync.md)
- [PRD_API_Spec_Compliance.md](PRD_API_Spec_Compliance.md)
- [PRD_API_Documentation_Fix.md](PRD_API_Documentation_Fix.md)
- [PRD_ApiResponse_Split.md](PRD_ApiResponse_Split.md)
- [PRD_Code_Standardization.md](PRD_Code_Standardization.md) / [PRD_Code_Structure_Cleanup.md](PRD_Code_Structure_Cleanup.md)

---

## 🐛 5. 버그 정정 PRD (~25개)

- [Action-Delete-404-Bug-Prd.md](Action-Delete-404-Bug-Prd.md)
- [Action-Event-Enum-Case-Fix-Prd.md](Action-Event-Enum-Case-Fix-Prd.md)
- [Action-Event-Fix-Prd*.md](.) (시리즈 4개)
- [Detection-Malfunction-Action-Query-Prd.md](Detection-Malfunction-Action-Query-Prd.md)
- [Event-Delete-Response-Prd.md](Event-Delete-Response-Prd.md)
- [Malfunction-POST-Duplicate-Debug-PRD.md](Malfunction-POST-Duplicate-Debug-PRD.md)
- [CameraEventMapping-Enum-Fix-PRD.md](CameraEventMapping-Enum-Fix-PRD.md)
- [Enum-Update-PRD.md](Enum-Update-PRD.md)
- [Integration-Model-Timezone-Fix-PRD.md](Integration-Model-Timezone-Fix-PRD.md)
- [ISO8601-DateTime-Format-PRD.md](ISO8601-DateTime-Format-PRD.md)
- [BUG_FIX_PLAN.md](BUG_FIX_PLAN.md)
- [PRD_ROI_Fix.md](PRD_ROI_Fix.md)

---

## 📊 6. 운영 / 회의 / 분석

- [20251208_GOP요구사항정리_GOP메인기능정의__통합_마크다운정리.md](20251208_GOP요구사항정리_GOP메인기능정의__통합_마크다운정리.md)
- [20260113_GOP회의안건.md](20260113_GOP회의안건.md)
- [API_Documentation.md](API_Documentation.md)
- [API_TEST_2026-01-30.md](API_TEST_2026-01-30.md) / [CheckList-2026-01-30.md](CheckList-2026-01-30.md)
- [AUDIT_LOG_SCREEN_DESIGN.md](AUDIT_LOG_SCREEN_DESIGN.md)
- [DB_Admin_Usage_Guide.md](DB_Admin_Usage_Guide.md)
- [Docker_Commands.md](Docker_Commands.md)
- [ActionEvent_Update_Logic_Review_Report.md](ActionEvent_Update_Logic_Review_Report.md)

---

## 🎨 7. UI / 디자인

- [GOP_MainControl_UI.md](GOP_MainControl_UI.md)
- [GOP_통제시스템_UI_연동설계.md](GOP_통제시스템_UI_연동설계.md)
- [GOP_통합상황도_스키마.md](GOP_통합상황도_스키마.md)
- [FIGMA_Lamp_Page_Guide.md](FIGMA_Lamp_Page_Guide.md)
- [FIGMA_Report_System_Design.md](FIGMA_Report_System_Design.md)

---

## 📐 8. 요구사항 / 기능 매핑

- [GOP_요구사항_통합정리.md](GOP_요구사항_통합정리.md)
- [GOP_과학화경계시스템_요구사항정리.md](GOP_과학화경계시스템_요구사항정리.md)
- [GOP_SVSS_기능매핑_분석.md](GOP_SVSS_기능매핑_분석.md)
- [GOP_개발항목_식별_및_범위산정.md](GOP_개발항목_식별_및_범위산정.md)
- [GOP_데이터관리_분류체계.md](GOP_데이터관리_분류체계.md)
- [GOP_Device_Refactoring_스키마.md](GOP_Device_Refactoring_스키마.md)
- [Device_Refactoring_Plan.md](Device_Refactoring_Plan.md) / [Device_Refactoring_Final_Report.md](Device_Refactoring_Final_Report.md)

---

## 🧪 9. 시뮬레이션 / 검증

- [sim/raw_data.json](sim/raw_data.json) — 19 시나리오 raw 데이터
- [sim/run_sim.ps1](sim/run_sim.ps1) — 시뮬레이션 실행 스크립트
- workflow_audit_v3/ — 9 agent 검증 raw

---

## 📦 10. 메모리 / 세션 관리

- [memory/session-context.md](memory/session-context.md) — 현재 세션 컨텍스트 (이 진입점)

---

## 🔍 11. Analysis 보고서 (v4.7+ 신설)

| 보고서 | 차수 | 핵심 |
|---|---|---|
| [Analysis/Account_Auth_Session_Analysis_v4.6.md](Analysis/Account_Auth_Session_Analysis_v4.6.md) | v4.7 | 30 endpoint × 10 feature 전수 조사 / 113 이슈 / Verdict FAIL / OWASP 41점 |
| [Analysis/Device_Delete_Response_Verification_v4.6.md](Analysis/Device_Delete_Response_Verification_v4.6.md) | v4.7+v4.8 | DELETE 응답 envelope 검증 + P0/P1 sweep (15 endpoint 정정) |

---

**문서 인덱스 버전**: v4.9 / **최종 갱신**: 2026-06-22 / **총 문서**: 143 파일
