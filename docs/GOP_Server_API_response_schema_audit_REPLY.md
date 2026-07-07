# GOP API Server — 응답 스키마 지뢰 전수 감사 결과 통지

- **작성일**: 2026-07-07
- **응답 대상**: 클라/배포 팀
- **응답 세션**: `pids-api-server` 서버 세션
- **커밋/태그**: `release/v6.0-cert_patch` 위 → `v6.0-response_schema_audit`
- **선행**: `servers_port_response_relax`, `users_role_response_relax`, `clone_deploy_bugfix`(#2 audit) — 같은 패턴을 3~4번 얻어걸려 수정한 뒤, 이번에 **예방 전수 감사**

---

## 📌 두괄식 결론

| 항목 | 결과 |
|---|---|
| 감사 방식 | 컨테이너 런타임 **introspection** — 모든 `*Response` pydantic 필드 ↔ SQLAlchemy 컬럼 타입 대조 |
| 스캔 규모 | `*Response` 스키마 91개, Enum 응답 필드 **~100건** |
| **발견 지뢰** | **21건** (String/JSON 컬럼 + strict Enum 응답 → 500 위험) |
| 안전 확인 | 77건 (DB `SQLEnum` 이 값 강제 → 완화 불요) |
| 처리 | 지뢰 21건 전부 **Enum → str 완화** (요청 스키마는 유지) |
| 검증 | introspection 재실행 **landmine 0** + 8 endpoint 회귀 200 |

**이제 clone 배포 시 옛/임의 값으로 인한 목록 API 500 이 원천 차단됩니다.**

---

## 1. 배경 — 같은 버그를 4번 얻어걸림

| 회차 | 필드 | 계기 |
|---|---|---|
| 1 | `ServerResponse.port` (ge=1) | 클라 리포트 |
| 2 | `AccountUserResponse.role` | 클라 리포트 |
| 3 | `AuditLogResponse.actor_role` | 클라 리포트 |
| 4 | (clone_deploy_bugfix #2 재확인) | 버그 리포트 |

전부 **"응답 스키마에 요청용 strict 제약(Enum)이 그대로 붙어 있고, DB 컬럼이 String 이라 제약 밖 값이 저장 가능 → 응답 직렬화 500, 목록이면 전체 죽음"** 구조. 두더지잡기로는 끝이 안 나서 **전수 감사**로 남은 지뢰를 한 번에 제거했습니다.

---

## 2. 감사 방법 (introspection)

```
1. 모든 SQLAlchemy 모델의 컬럼 타입 수집  {모델: {컬럼: 타입}}
2. 모든 *Response pydantic 스키마의 Enum 필드 수집
3. 스키마 클래스명 → 모델 매핑 (CameraResponse → Camera 등)
4. 판정:
   - 응답 Enum 필드 + 대응 DB 컬럼이 String/JSON  → *** LANDMINE ***
   - 응답 Enum 필드 + 대응 DB 컬럼이 SQLEnum      → safe (DB가 값 강제)
```

핵심 통찰: **DB 컬럼이 `SQLEnum` 이면 애초에 잘못된 값이 저장될 수 없어 응답 Enum 도 안전**. 지뢰는 오직 `String` 컬럼에 Enum 값을 담는 조합.

---

## 3. 발견된 지뢰 21건 + 완화

| 파일 | 스키마.필드 | 원 Enum |
|---|---|---|
| `report.py` | ReportGeneration(List)Response.**report_type/period_type/status** | EnumReportType/Period/Status |
| | ReportTemplate(List)Response.**report_type/default_period** | EnumReportType/Period |
| | ReportPreviewResponse.**period_type** | EnumReportPeriod |
| `event.py` | DetectionEvent/LogResponse.**type_event/action_reported/result** | EnumEventType/TrueFalse/DetectionType |
| | MalfunctionEventResponse.**type_event/action_reported/reason** | EnumEventType/TrueFalse/FaultType |
| | Connection/ActionEventResponse.**type_event** | EnumEventType |
| `user.py` | UserLoginLogResponse.**action/result/failure_reason** | EnumLoginAction/Result/FailureReason |
| | UserSessionResponse.**logout_reason** | EnumLogoutReason |
| `audit_log.py` | AuditLogResponse.**action_status** | EnumAuditStatus |

**모두 응답 필드를 `Enum` → `str` 로 완화** (요청/Create/Update 스키마는 strict Enum 유지 — 새 데이터 위생).

### 특히 주목 — Report 계열
방금 `v6.0-report_date_range` 에서 `period_type="custom"` 을 추가했는데, **옛 report_generations 행엔 그 값이 없거나 다른 값**일 수 있어 목록 500 지뢰였습니다. 이번 완화로 함께 제거.

---

## 4. 클라 영향 — 없음

- 응답 JSON 값은 **동일한 문자열** (`"ADMIN"`, `"7d"`, `"Intrusion"` 등). Enum이든 str이든 직렬화 결과 같음.
- 유일한 변화: Swagger 문서에서 해당 필드의 **enum 허용값 목록 표시가 사라짐** (제약이 str로 완화됐으므로).
- 클라 역직렬화가 문자열을 받으므로 **하위호환 100%**.

---

## 5. 검증 (2026-07-07)

| 검증 | 결과 |
|---|---|
| introspection 재실행 | **LANDMINE 21 → 0** |
| GET /reports/generations · /reports/status | 200 |
| GET /events/detections · malfunctions · actions · connections | 200 |
| GET /audit-logs · /users | 200 |
| unknown 2건 (`DeviceNestedResponse.category/mode`) | Camera 모델이 `SQLEnum` 소스 → 안전 확인 (완화 불요) |

---

## 6. 재발 방지 (정책 확정)

1. **응답 스키마(`*Response`)에는 Enum/제약을 붙이지 않는다** — 값 검증은 요청(Create/Update)과 DB 계층에서. 응답은 관대(Postel's Law).
2. **DB 컬럼이 `SQLEnum` 이면 응답 Enum 도 안전** — DB가 값을 강제하므로. String 컬럼일 때만 위험.
3. **신규 `*Response` 필드 추가 시 이 introspection 스크립트로 회귀 검사** (`scripts/` 편입 검토).
4. **장기(별도 사이클)**: String 컬럼을 `SQLEnum` 으로 승격하는 마이그레이션 검토 — 근본적으로 DB 레벨에서 값을 강제하면 응답 완화 자체가 불필요. 단 파괴적이라 데이터 정리 병행 필요.

---

## 7. 참조

- **선행 REPLY**: `servers_port0`, `users_role_response_relax`, `clone_deploy_bugfix`
- **서버 커밋**: 태그 `v6.0-response_schema_audit`
- **CHANGELOG**: `CHANGELOG.md` → v6.0-response_schema_audit
- **수정 파일**: `app/schemas/report.py`, `event.py`, `user.py`, `audit_log.py`
- **저장소**: origin=`github.com/lsirikh/GopApiServer`, gitea=`192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server`
