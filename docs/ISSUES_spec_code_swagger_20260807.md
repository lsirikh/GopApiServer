# GOP API 서버 — 이슈 등록부 (명세↔코드↔Swagger 3자 정합)

- **작성일**: 2026-08-07
- **근거**: 멀티에이전트 정밀감사 26에이전트 / **977항목 점검** / 확증 갭 **103건**
- **소스**: 코드 `app/`(진실 소스) · 명세 `GOP_Restful_Api_연동설계.md`(16.7K줄) · **라이브 Swagger 실덤프**(251 오퍼레이션·292 스키마, v6.3.2)
- **검증**: 도메인별 **적대적 반증관**이 재검증 — CONFIRMED 85 · PARTIAL 11 · [미검증] 7 (REFUTED는 전량 제외)
- **원본 분석**: [spec-code-swagger-triangulation.md](analyses/spec-code-swagger-triangulation.md)

---

## 0. 두괄식 — 판정

**명세는 최신이 아니며, 3개 축이 서로 어긋나 있다. 특히 P0 14건 중 3건은 지금 배포에서 실제 사고를 낼 수 있다.**

| 지표 | 값 |
|---|---|
| 확증 갭 | **103건** — P0 **14** · P1 **50** · P2 **39** |
| 축 분포 | 명세 오류 **68** · Swagger 미노출/오문서 **17** · **코드 결함 12** · 코드-명세 불일치 6 |
| 무결 확인 | §11 Tracking 전항목 · §8.8 proxy-settings · Swagger 빈스키마 36건(enum이라 정상) |

### 즉시 위험 3가지

| # | 위험 | 실제 영향 |
|---|---|---|
| 1 | **§8.6.4 메트릭 삭제 오계약** | 명세는 `before_date`, 코드는 `older_than_days`. 명세대로 호출 시 파라미터가 **무시**되고 **기본 30일치 메트릭 비가역 전량 삭제** |
| 2 | **RBAC 양방향 붕괴 (실발생 중)** | ① `integrations`/`files`가 `EnumPermissionModule`에 없어 **16개 쓰기 라우트가 비-ADMIN 영구 403** ② 동시에 §7 서브리소스 12경로 + §5 ROI/XyPoint/그룹멤버십 10경로는 **인가 무검사 통과** |
| 3 | **Swagger 응답 계약 공백** | 2xx 빈 스키마 **71/251(28.3%)**, 422가 실응답과 다른 형식으로 **234건** 오문서, 401·403·500·503 **0건**, reports `response_model` **0건** → .NET 클라 codegen 무력화 |

---

## 1. P0 — 즉시 조치 (14건)

| # | § | 이슈 | 축 | 조치 |
|---|---|---|---|---|
| P0-1 | §8.6.4 | `before_date`(명세) vs `older_than_days`(코드·Swagger) — **30일치 전량 삭제 유발** | 명세 오류 | L13797-13800 Query 표 교체 + ChangeLog L16741 동반 정정 + 삭제 기준 컬럼 `created_at` 명시 |
| P0-2 | §7/§9.4.7 | `integrations`·`files` 모듈이 `EnumPermissionModule`에 부재 → 16 라우트 비-ADMIN 영구 403 | **코드 결함** | `enums.py:842-855`에 2종 추가(12→14)+그룹 매트릭스 마이그 / 또는 기존 어휘 재배정 → **결정 필요** |
| P0-3 | §7 | 서브리소스 단건 PATCH·PUT·DELETE + bulk **12경로 인가 무검사 통과** | **코드 결함** | `permission_map.py` Integrations 블록에 12항목 추가(cameras/lamps/speakers × edit·delete) |
| P0-4 | §12 | 405·미매칭 404가 커스텀 엔벌로프 이탈 → `{"detail":...}` 유출 | **코드 결함** | `main.py:16,607` 핸들러를 `starlette.exceptions.HTTPException`에도 등록 |
| P0-5 | §12.1 | 422가 `HTTPValidationError`로 **234건** 오문서(실응답과 완전 상이) | Swagger 오문서 | `main.py` FastAPI에 `responses={422: ValidationErrorResponse}` 전역 + `common.py:134-148`에 `meta` 추가 |
| P0-6 | §10 전역 | reports 라우터 `response_model` **0건** → 응답 계약 Swagger 0% | Swagger+코드 | 17 라우터에 부착, 미등재 스키마 9종 해소, `:49/:51` dead import 정리 |
| P0-7 | §10.4.1/§13.1 | reports 미문서 엔드포인트 **4건**(cancel·DELETE·detail.csv·preview/{id}) | 명세 오류 | §10.4.1 표 4행 + §10.4.7~10.4.10 신설 + §13.1 부록 4줄 |
| P0-8 | §10.4.5 | `preview` 응답 본문 구조가 **정반대** | 명세+코드 | 명세를 코드 실반환 7키로 교체 + `schemas/report.py:267`에 `report_type` 추가 선행 |
| P0-9 | §6.2.5 | Malfunction PUT `action_reported` "무시됨"(실제 **422**) | 명세 오류 | L8335·L8350 "전송 시 422" 통일 + §6.1.5·§6.3.5 동일 주의문 |
| P0-10 | §6.4.5 | Action PUT `from_event_id` 잔존(전송 시 422) | 명세 오류 | L9337-9367에서 삭제 → 3필드. 08-04 P0 정정이 actions만 누락한 잔여분 |
| P0-11 | §5.5.4 | Enclosure PATCH `door_status`·`type_device`(extra=forbid → 422) | 명세+Swagger | 명세 예시·표 행 삭제 + `enclosures.py:321` docstring 삭제 |
| P0-12 | §5.5.13 | `GET /api/enclosure-metrics` 계약 전면 불일치(쿼리 5종·응답 shape) | 명세 오류 | 코드 실제 shape로 정정. 페이징이 실요구면 구현 → **결정 필요** |
| P0-13 | §5.9.1 | `GET /rois/{id}/points` 응답 키 `points`(명세) vs `items`(코드) + 쿼리 미기재 | 명세 오류 | `data:{items,total}`로 정정 + Query 표·pagination 신설 |
| P0-14 | §7.3.1/§7.5.1 | 서브목록 응답 봉투 불일치(잉여 `pagination`) | 명세 오류 | `data:{items,total}`로 통일, pagination 블록 삭제 |

---

## 2. 코드 결함 (명세가 아니라 코드를 고쳐야 함) — 12건

| # | 위치 | 내용 | P |
|---|---|---|---|
| C-1 | `enums.py:842-855` | `INTEGRATIONS`/`FILES` 부재 → 16 라우트 영구 403 (**실발생**) | P0 |
| C-2 | `permission_map.py` | Integrations 서브리소스 **12경로 미등록** → 무검사 통과 | P0 |
| C-3 | `main.py:16,607` | starlette HTTPException 핸들러 미등록 → 405/404 엔벌로프 이탈 | P0 |
| C-4 | `permission_map.py` | ROI 4(`rois.py:191/267/348/444`)·XyPoint 3(`xypoints.py:100/167/231`)·그룹멤버십 3(`device_groups.py:705/793/899`) **10경로 미등록** | P1 |
| C-5 | `event_mapping_lamps.py:214` | 중복 매핑 사전조회 부재 → UNIQUE 위반이 **500**(409여야) | P1 |
| C-6 | `system_events.py:160-199` | 목록 pagination 미계산 → 항상 null | P1 |
| C-7 | `schemas/report.py:267,336` | `ReportPreviewResponse.report_type` 누락(응답 잘림), `ReportGenerationResponse` progress 5필드 누락 + 미반환 4필드 보유 | P1 |
| C-8 | `schemas/settings.py:31` | `SessionSettingsUpdate` extra 미차단 → 오타 키가 조용히 200 | P2 |
| C-9 | `schemas/event.py:80,245` | 요청 `result`/`reason`이 str → Swagger enum 미노출 + "요청 strict" 정책 이탈 | P2 |
| C-10 | docstring/주석 일괄 | `enums.py` 개수 오기 4곳(18→21, 19→21, 25→26, 4→5), `reports.py:795/:170`, `schemas/user.py:50`(8종), `server_metrics.py` `_to_naive_kst`(실체 to_utc) 등 | P2 |
| C-11 | dead 코드 | `reports.py:49/51`·`cameras.py:25` dead import, `EventMappingCameraNestedResponse` 미참조, `EnumChartType` 사용 0, `preview.html`+Jinja2 사문화 | P2 |
| C-12 | `grants.py:166-167` | page/size에 `ge/le` 미지정 → Swagger 경계 미노출 | P2 |

---

## 3. Swagger 전용 문제 — 12건

| # | 내용 | 조치 지점 | P |
|---|---|---|---|
| S-1 | 422 오문서 **234건** | `main.py` 전역 `responses` + `ValidationErrorResponse`에 meta | P0 |
| S-2 | reports `response_model` 0건, 미등재 스키마 9종, download/detail.csv가 json 오표기 | `reports.py` 17 라우터 | P0 |
| S-3 | 2xx 빈 스키마 **71/251** (우산 항목) | 아래 S-4~S-7이 실체 | P1 |
| S-4 | §7 서브리소스 **21 라우트** `ApiSingleResponse[dict]` | `event_mapping_{cameras,lamps,speakers}.py` | P1 |
| S-5 | System Events **7 라우트** 미부착 | `system_events.py` 73/133/202/229/278/323/364 | P1 |
| S-6 | Enclosure Metrics 4 + `cameras/{id}` + `device-groups/{id}` | `enclosure_metrics.py`, `cameras.py:291`, `device_groups.py:148` | P1 |
| S-7 | Settings 2 + Grants 4 + UserGroups 7 + Users 7 응답 스키마 부재 | 해당 라우터 | P1~P2 |
| S-8 | 401·403·500·503 응답 **0건**, `ApiErrorResponse` 참조 0 | **전역 `responses` 기본값 도입**(개별 땜질 금지) | P1 |
| S-9 | 억제 **202** 응답이 3개 이벤트 POST에 미노출 → 재전송 폭주 위험 | `detections/malfunctions/connections` POST | P1 |
| S-10 | download 200 json 오표기 + 400/404/**410** 미선언 | `reports.py` download | P1 |
| S-11 | `X-Client-Id` 헤더 미선언 + login docstring client_id 누락 | `auth.py` login | P2 |
| S-12 | `GET /api/grants` page/size 경계 미표기 | `grants.py:166-167` | P2 |

---

## 4. 명세 오류 (68건) — 섹션별 요약

| § | 건수 | 대표 이슈 |
|---|---|---|
| §3·§12 | 9 | 에러코드표 유령코드(`DB_ERROR`·`TIMEOUT`) / 422 코드명(`UNPROCESSABLE_ENTITY`→`VALIDATION_ERROR`) / `field_errors` 유령 필드 / 204 미사용·202 누락 / 타임스탬프 `Z`→`+09:00` 27줄 |
| §4 Enum | 8 | `EnumDeviceCategory` LAMP 누락(4곳) / `EnumAuditActionType` 18→21 / `EnumReportPeriod` custom / `EnumReportStatus` CANCELLED / `EnumPermissionModule` 8→12 / Suppression 4종 §4 부재 |
| §5 Device | 12 | `threshold_config` 키 3종 오기(무증상 오설정) / Speaker·Camera PATCH `type_device` / ROICreate 필수 역전 / Lamp `user_password` "보안상 제외" 오서술 / Preset `is_restricted_zone` 누락 |
| §6 Event | 11 | SYNC_DETECTION 발행 계약 본문 부재 / `start_date`·`end_date` required 오표기 + 순서검증 422 유령 예시 / `frame_width/height` 예시 전무(6곳) / message 문자열 불일치 |
| §6.8 억제 | 3 | `recurrence_rule` 필드표 누락+미구현 경고 / PATCH 400 미기재 |
| §7 통합 | 6 | 서브목록 봉투 / page·limit 유령 쿼리 + 유령 422 예시 / bulk 중복 처리 서술 / `failed_items` 자기모순 |
| §8 서버 | 12 | `type_server` 필터 누락 / DELETE 응답 `data:{id}`→null(2곳) / §8.3.7 페이징·필드·message 전면 / `collected_at` 저장형 오서술 / `start_date`→`start_time` |
| §9 계정 | 10 | users 표 권한열 전부 ADMIN / 중앙 매트릭스 집행 모델 부재 / grant 인가 서술 stale / §9.9.5 절 배치 오류 / 라인번호 5개 stale |
| §10 리포트 | 6 | 컴포넌트 15종→21종 / templates 목록=상세 복사본 / generate start_date·end_date / DELETE 응답 형식 |
| §13.1 부록 | 1 | Swagger 251 대비 **미등재 19건**(역방향 유령 0) |

---

## 5. 결정 필요 (13건) — 사람이 정해야 함

| # | 사안 | 선택지 |
|---|---|---|
| D-1 | **integrations/files 권한 모듈** | (A) enum 2종 추가(12→14)+매트릭스 마이그 / (B) 기존 어휘 재배정 / (C) ADMIN 전용이 의도면 명세 명시 |
| D-2 | `EnumAuditActionType` 개수 | 21종(GRANT_* 3) vs 23종(`USER_PHOTO_*` 2종 승격) |
| D-3 | Suppression enum 배치 | (A) §4.10 신설 / (B) §6.8 인라인 유지 + 참조 문구 1줄 수정 |
| D-4 | §5.5.13 enclosure-metrics 페이징 | 명세를 코드에 맞춤 vs 라우터에 페이징 구현 |
| D-5 | §6.1.1 `type_event` 쿼리 | 코드에 필터 추가(대칭) vs 명세 예시 삭제 |
| D-6 | ROI/XyPoint/그룹멤버십 module 귀속 | `devices` vs `cameras` |
| D-7 | §10.3.4 templates 길이 제약 | 스키마 Field 강화 vs 명세에서 삭제 |
| D-8 | §6.1/§6.2 `detail` 타입 | Detail 스키마 적용 vs "자유형 JSONB" 명기 후 미사용 클래스 삭제 |
| D-9 | POST extra 정책 | 코드 `extra="forbid"` 강화(회귀 리스크) vs 명세에 ignore 명기(권고) |
| D-10 | 카메라 PUT semantics | `EventMappingCameraCreate` 재사용 → Replace 스키마 분리 여부 |
| D-11 | §8.6 시간 기준 컬럼 | `created_at` 유지(명세 명시) vs `collected_at` 전환(계약 변경 → 별도 PRD) |
| D-12 | 인가 서술 부록 범위 | §7.1 표 단독 vs `permission_map.py` 전체(≈100항목) 1:1 매핑 |
| D-13 | 전역 `responses` 기본값 | 공통 에러 스키마 전역 등록(권장) vs 라우터별 개별 |

---

## 6. 권고 실행 순서

| 단계 | 범위 | 이유 |
|---|---|---|
| **1** | P0-1(§8.6.4) + P0-2·3(RBAC) + P0-4(405) | 실사고/실발생. **D-1 결정 선행 필요** |
| **2** | P0-5(422 전역) + S-8(에러 전역) | 한 번의 전역 설정으로 234+건 동시 해소. **D-13 결정** |
| **3** | P0-6~8(reports) + S-2 | reports 도메인이 Swagger 0% — codegen 최대 피해처 |
| **4** | P0-9~14(명세 계약 파손 6건) | 명세대로 호출 시 422 나는 오문서 |
| **5** | 명세 오류 68건 일괄 | 하루 1버전 원칙으로 ChangeLog 1블록 |
| **6** | P2·코드 주석·dead 코드 | 저위험 정리 |

> **하네스 규율**: 각 단계마다 5중싱크(코드·Swagger·명세·이미지·컨테이너) 검증, 명세는 전체 구조 확인 후 해당 파트 수정 + 하단 ChangeLog에 **하루 1버전**으로 누락·중복 없이 기재.

---

## 7. 재작업 금지 (반증으로 제외된 오탐)

- `event_mapping_*` **21개소 meta 누락** → 오탐(`response_model`로 자동 주입)
- **502 BAD_GATEWAY**·**405** 에러표 추가 → 금지(전자는 죽은 매핑, 후자는 코드 사안)
- **응답 enum str 완화**를 결함으로 보고 → 금지(의도적 트레이드오프). 남는 건 `EnumChartType` 1건
- **Suppression 파생 매핑이 코드에만 존재** → 오탐(ChangeLog L16640에 전문 존재)
- **§5 speakers/enclosures/lamps/device_groups/camera_presets RBAC 무보호** → 오탐(중앙 enforce_matrix로 보호). `enclosure_metrics`는 **의도된 제외**
- **Tracking(§11) 전항목**·**§8.8 proxy-settings** → 3자 완전 정합, 조치 없음
- Swagger `props=(EMPTY)` **36건** → 전부 enum 타입 스키마로 **정상**
- 수치 정정: 빈 스키마 75→**71**, meta 누락 52→**43**, 422 오문서 232→**234**, §5 RBAC 다수→**10경로**
