# Session Context — GOP RESTful API Test Server

> 매 작업 후 갱신 (CLAUDE.md 규약). 다음 세션이 현재 상태를 빠르게 파악하기 위한 단일 진입점.
>
> 🤝 **멀티세션 동시작업 중 — 작업 전 반드시 [SESSION_COORDINATION.md](SESSION_COORDINATION.md) 읽기** (소유권 경계: ★`auth.py`는 WS-B 스케쥴링 세션 단독, WS-A RBAC 베이스 동결).

---

## 현재 차수 (HEAD)

| 항목 | 값 |
|---|---|
| **차수** | **v5.3** (2026-07-02, **Legacy User 완전 삭제 + AccountUser 통일** — GIS 팀 요청 대응, 14/14 PASS) / v5.2 (2026-06-30, hotfix + Force-Logout P1 + Session-Settings P2 + 휴면 RBAC 부착) / v5.1 (2026-06-29, RBAC Enforcement) / v5.0 (2026-06-29, 그룹 권한) |
| **HEAD commit** | `fc512b3` (docs(v5.3): .NET/GIS 팀 통지 문서 — DOC-03) |
| **branch** | `feature/report-master-redesign` (공유 작업트리) — ✅ **Gitea v4.8 + origin 모두 push 완료** (v5.3 마감 fc512b3 반영). 태그 `v5.3-final-stable`(b757325a) + `pre-legacy-user-removal` |
| **Container** | ✅ **v5.3 5-sync 완료** (2026-07-02) — Image rebuild + healthy + **Swagger version=5.3.0** 라이브 + API Version 5.3. **DB `users` 테이블 DROP 완료** (v56 마이그레이션). |
| **DB** | PostgreSQL 16 / **`users` 테이블 DROP** (v5.3 v56 마이그레이션, FK 파괴 0) + `account_users` 8건 유지 + `app_settings` 등 v5.2 이전 상태 유지. |

---

## 이번 세션 (v5.2 — 2026-06-30, .NET 이관 PRD 2종)

> .NET 클라팀 이관 서버 PRD 3종(`docs/prds/PRD_GOP_Server_*.md`) 중 실행 2종 완료. 계약 4건 PM 확정.

### 완료 + 커밋 (로컬, tests/는 .gitignore라 미커밋)

- **P1 Force-Logout (Phases 0-5)** — `f00f7ca`(구조: token_blacklist id cross-dialect) + `4ff9a05`(FR-SVF-01~12) + `785c313`(FR-SVF-10 401 SESSION_REVOKED).
  - logout이 access+refresh 패밀리 무효화(구멍 차단) / force_logout last-ADMIN 가드 / sid 클레임(=UserSession.id)·login·refresh session_id / RevokePayload+HMAC 서명 / per-session NATS publisher(게이트 off) / 401 안정코드.
  - 로컬 27건 PASS.
- **P2 Session_Settings (FR-SVS-01~06)** — `73ecc5e`. app_settings + settings_service + GET/PUT /api/settings/session(require_admin) + auth.py 런타임 만료·잠금임계 + ConfigChangeLog 감사 + v55 마이그레이션. 로컬 11건 PASS.
- **전체 회귀 0**: 전체 스위트 174 failed(전부 사전 실패 = pydantic/env, P1+P2 전과 동일 -1) / 2244 passed.

### 확정 계약 4건 (클라 짝 PRD 통지 대상)

1. session_id = JWT `sid`(=UserSession.id) + login/refresh 응답 필드. refresh 시 sid 고정·jti 회전.
2. revoke subject = `sensorway.{unit}.account.{user_id}.session.{session_id}.revoke` (광역 금지).
3. payload = HMAC-SHA256 + 전용 REVOKE_SIGNING_KEY, canonical(sorted·compact·UTF-8·null 명시), reason=EnumLogoutReason.
4. revoked → 401 `error.code=SESSION_REVOKED`(403=권한부족 구분).

---

## 나머지 작업 (다음 세션) ★

> **2026-06-30 추가 세션**: ✅ **D 부분완료**(origin push 완료, **gitea만 인증실패로 잔여**) + ✅ **C 완료**([CONTRACT_GOP_Server_v5.2.md](../prds/CONTRACT_GOP_Server_v5.2.md), 골든벡터 실코드 계산) + ✅ **A 안전분 FR-SV-10 완료**(`b2f80c8`).
>
> ★ **A 실상 재검증(2026-06-30)**: 코드가 세션컨텍스트보다 앞섬. **RBAC 인프라 전부 구축됨**(`require_perm`·`require_admin`·`get_current_account_user_optional`·jti 검사 auth.py). **FR-SV-01**(세션 require_admin 4종 + 벌크 jti)·**FR-SV-05**(enums)·**FR-SV-06**(마지막 ADMIN FOR UPDATE 가드, users.py:529) **이미 구현 확인**. **FR-SV-10 이번 세션 구현**. **남은 핵심=파괴적 부분**: require_perm 8도메인 부착 + 30 라우터 이주(현 `.env AUTH_MODE=public`이라 부착 즉시 Bearer 없는 클라 401). require_perm은 reports.py만 부착됨.

| # | 작업 | 분량/유형 | 비고 |
|---|------|---------|------|
| **A** | **RBAC_Enforcement — 휴면 부착 완료, 활성화만 게이트** | 대형 / plan: [RBAC_Enforcement-prd-plan.md](../plans/RBAC_Enforcement-prd-plan.md) | ✅ **휴면(dormant) RBAC 부착 완료**: `c49f0a4`(구조 헬퍼) → `require_perm_optional` 추가 → `9a6624c`(27 write 데코레이터 부착) + `b2f80c8`(FR-SV-10). `require_perm_optional`=**AUTH_MODE=public 무집행(현 동작 보존)**·token 플립 시 활성. 도메인 회귀 0(사전실패 카운트 전후 동일), 단위 5/5 PASS. ★**P5 활성화=게이트**: 클라(.NET 3종) Bearer 동시배포 확인 후 `.env AUTH_MODE=public→token` 플립(분리 시 전원 401, 롤백=public 복귀). ✅ **P8 FR-SV-09 종결**(`de4266d`: user_groups POST/PUT/DELETE/GET-members require_admin). ✅ **P6 FR-SV-07 DB레벨 이미 충족**(`trg_audit_logs_immutable` v51 트리거 — DELETE/UPDATE 거부, FK익명화 예외); 잔여=export/retention 엔드포인트 + purge(purge는 WS-B sweep 영역). **P7 FR-SV-11(RTSP 마스킹)=반파괴·클라(Rtsp.Viewer.Ui) 조율 게이트로 보류**. |
| **B** | **Force-Logout 활성화 (FR-SVF-08 + 게이트)** | 인프라+조율 | NATS 발행 ACL(서버만 account.> publish, 클라 subscribe-only) + 클라 subject 매칭 확인(V-SVF-05) → 확인 후 `.env NATS_REVOKE_ENABLED=true` + 실 REVOKE_SIGNING_KEY 배포. **계약 §6 B-1~B-3에 명시** |
| ~~**C**~~ | ~~클라 회신용 계약 스냅샷 문서~~ | ✅ **완료** | `docs/prds/CONTRACT_GOP_Server_v5.2.md` — C1 sid / C2 subject / C3 payload+골든벡터 V1·V2 / C4 401 / P2 GET·PUT 스키마. 클라 짝 PRD 통지 + §6 B-1(subject 매칭) 회신 요청 |
| **D** | **푸시** | 소 | ✅ origin(GitHub) push 완료(7건). ⬜ **gitea 잔여** — 인증실패(http://192.168.202.160:3000). 차장님 직접: `! git push gitea feature/tracking-gis-ingest` |
| ~~**E**~~ | ~~배포(5-sync)~~ | ✅ **완료 (5/5)** | 도커 재빌드(`api-server`) + 컨테이너 재기동(healthy) + app_settings 라이브 + Swagger 5.2.0 라이브 + 태그 `v5.2-pre-deploy`/`v5.2-deployed` + 롤백이미지 `pre-v5.2` + **명세서 본문 v5.2 동기화(`36379e3`)**. 5중싱크 전부 충족. |
| **F** | (별도) 사전 테스트 실패 174건 | 별도 결정 | server_schema(pydantic AttributeError)·logs_router·config_change_log·test_config = pydantic 버전/환경 이슈, 본 작업 무관 |

---

## v4.7 + v4.8 차수 핵심 (이번 작업)

### v4.7 (2026-06-21) — Account 분석 + DELETE P0

- **Workflow 13 agent** Account/Auth/Session 전수 조사 (1.15M token / 12분)
- **이슈 113건** (critical 13 / high 38 / medium 39 / low 23) — Verdict **FAIL**
- 평균 완성도 62.5% / OWASP 41점
- DELETE P0 정정 4건: Lamp/DeviceGroup/Server/ServerCategory → `data: null`
- 보고서: `docs/Analysis/Account_Auth_Session_Analysis_v4.6.md` (16KB)
- 보고서: `docs/Analysis/Device_Delete_Response_Verification_v4.6.md` (9KB)
- 안전점: `pre-delete-sweep` @ `a9ef6d6`

### v4.8 (2026-06-22) — DELETE P1 sweep

- 클라이언트팀 보고서 v2 §6 P1 11 endpoint 일괄 정정
- EM 단건 DELETE 3건 (Phase 9 `'data': {}` 정책 정정)
- 일반 단건 DELETE 8건 (Reports/Users/UserGroups/UserSessions ×3/ServerMetrics/EnclosureMetrics)
- envelope 표준화: `{success, message, data:None}` + 정보는 message에 보존
- OpenAPI 전수 검증: dict 잔존 **0건**, NoneType 통일 22개

---

## v4.6 ~ v4.8 git 이력

```
5263317  fix(delete): P1 sweep — 11 endpoint                    ← HEAD / v4.8-final-stable
0b3ea1a  fix(delete): P0 4 endpoint (Lamp + DG + Server + SC)   ← v4.7-final-stable
a9ef6d6  docs(Analysis): Account/Auth/Session 분석              ← pre-delete-sweep
7bbc1be  docs(v4.6): CLAUDE.md 규약 정정 (session-context + INDEX)
3592a9d  docs(v4.6): README v1.9→v4.6 + CHANGELOG.md
536c0b8  feat(v4.6): Phase 10 시드 + pagination 검증
0d74cbc  docs(v4.6): 명세 헤더 정정
bb49462  refactor(v4.6): Camera Preset 단순화
bdf12c1  feat(v4.6): Critical 8건 + Camera Preset
```

---

## 안전점 5단

| 시점 | 태그 | commit |
|---|---|---|
| **v4.8 최종** | `v4.8-final-stable` | (신설) |
| v4.7 최종 | `v4.7-final-stable` | `0b3ea1a` |
| DELETE 작업 직전 | `pre-delete-sweep` | `a9ef6d6` |
| v4.6 최종 | `v4.6-final-stable` | `7bbc1be` |
| v4.5 마감 | `v4.5-final-stable` | `e7a611e` |
| v4.4 마감 | `v4.4-final-stable` | `050cf6d` |

---

## OpenAPI DELETE 전수 검증 (v4.8 완료 시점)

| 분류 | 카운트 |
|---|---|
| ✅ `ApiSingleResponse_NoneType_` (data: null 통일) | **22** |
| ❌ `ApiSingleResponse_dict_` 잔존 | **0** |
| 🟡 $ref 없음 (response_model 미부착) | 14 (v4.9+) |
| 🟡 `Union[dict,None]` events 4건 | (보고서 §6 미명시, 별도) |

---

## v4.9+ 잔존 작업

| 항목 | 분량 | 우선순위 |
|---|---|---|
| **RBAC 의존성 신설** (require_admin/require_role) | 6h | critical (v4.7 Top 권고 #1) |
| **세션 활성 검증** (get_current_account_user) | 6h | critical (Top 권고 #2) |
| **Refresh token type 검증** + rotation/blacklist | 8h | critical (Top 권고 #3) |
| **AuditLog 본문 보강** + 누락 해소 | 10h | high (Top 권고 #4) |
| **비밀번호 정책** + 변경 시 세션 무효화 | 15h | high (Top 권고 #5) |
| FR-11 JWT jti 블랙리스트 (logout 무효화) | 4.5h | 보안 |
| DELETE $ref 없음 14건 response_model 부착 | 별도 PRD | medium |
| Union[dict,None] events 4건 sweep | 30분 | low |
| M04 enclosure-metrics envelope (v4.7 분리됨) | 3h | high |

→ v4.9 ~ v5.0 **보안 강화 차수** 권고 (Top 5 모두 적용 시 ~45h)

---

## 매니저 통합 가이드 단일 진입점

| 정보 | 위치 |
|---|---|
| 빠른 개요 + 시드 명세 | [README.md](../../README.md) (v4.10) |
| 전체 차수 이력 | [CHANGELOG.md](../../CHANGELOG.md) |
| API 명세 | [GOP_Restful_Api_연동설계.md](../../GOP_Restful_Api_연동설계.md) (v4.10) |
| DB 스키마 | [GOP_스키마_전체.md](../GOP_스키마_전체.md) (v2.12) |
| Camera Preset 감시금지구역 | [v46_camera_preset_restricted_zone_guide.md](../v46_camera_preset_restricted_zone_guide.md) |
| **Account/Auth/Session 분석** | [Account_Auth_Session_Analysis_v4.6.md](../Analysis/Account_Auth_Session_Analysis_v4.6.md) |
| **DELETE 응답 검증 보고서** | [Device_Delete_Response_Verification_v4.6.md](../Analysis/Device_Delete_Response_Verification_v4.6.md) |
| docs/ 전체 인덱스 | [INDEX.md](../INDEX.md) |

---

## 최근 작업 흐름

```
2026-06-17  v4.3 마감 — Bulk API 7건 + ActionEvent 1:N
2026-06-18  v4.4 마감 — Phase 1~5 + multi-line Column + user_password 복원
2026-06-19  v4.5 마감 — minimal 6 그룹
            v4.6 마감 — Critical 8건 + Camera Preset + 시드 + pagination
2026-06-21  v4.7 마감 — Account 분석 (FAIL) + DELETE P0 4건
2026-06-22  v4.8 마감 — DELETE P1 sweep 11건 + Phase 8~12-7 (Event 정밀 + 불변성)
2026-06-24  v4.9 진행 — Phase 0 .NET 31건 회신 → Phase 1 Followup PRD → Phase 2~4 Auth/RBAC/Photo (17/17 PASS) → Phase 5 SEC-1 user_password 마스킹 (.NET v4.9 Review 회신, 8/8 PASS)
2026-06-25  v4.10 Phase 1 — SEC-1 마스킹 폐기 / 평문 회귀 (복호화 경로 부재, 차장님 결재 "그냥 평문으로 보내", 6/6 PASS)
            v4.10 Phase 2 — HTTPS 도입 (mkcert 폐쇄망) + Inno Setup rootCA 인스톨러 (6/6 PASS, 차장님 결재 "가장 간단·신뢰·폐쇄망")
            v4.10 Phase 2-add — PS2EXE Lite 인스톨러 2종 (certs/server_install.exe + client_install.exe, 차장님 결재 "두 개로 패키지해서 쉽게 쓸 수 있게")
2026-06-30  권한그룹 스케쥴링 분석 + PRD(Draft) — 현행 권한그룹 구조 교차검증(등급↔그룹 Option A 연계 확인, time_restriction/기간컬럼/스케줄러 전무, require_perm 부착 0건) → 옵션B(user_group_grants 부여 테이블) 결재 → docs/prds/PRD_Permission_Group_Scheduling.md 작성. 선결=RBAC 집행(PRD_GOP_Server_RBAC_Enforcement). 승인 대기
```

## 활성 PRD

- **활성 PRD**: `docs/prds/PRD_Permission_Group_Scheduling.md` (Draft, Phase=prd, Track C)
- **다음 할 일**: 사용자 승인(`advance-phase.js approve prd`) → plan 스킬로 구현 계획
- **핵심 기술결정**: 스케쥴은 부여(grant)에 건다(그룹 정의 아님) / 권위판정=request-time `valid_until>now`(sweep 비의존) / 등급매트릭스 ∪ 유효grant 합집합 / 선결=RBAC 집행 0%→집행 활성화

---

## 다음 세션 진입 시 권고

1. 이 파일(`session-context.md`) 읽고 위 **"나머지 작업 (다음 세션)"** 표(A~F) 확인
2. `git log --oneline -8` — v5.2 커밋 4건 확인 (HEAD `73ecc5e`)
3. 우선순위 권고: **D 푸시** + **C 클라 계약 통지** 먼저(소) → **B Force-Logout 활성화**(클라 subject 확인 필요) → **A RBAC 잔여**는 plan부터(대형, 클라 Bearer 동시배포 조율)
4. ★ 본 세션 작업은 **로컬 코드/테스트만** — 배포(E: 도커 재빌드·마이그레이션·태그) 미수행. `tests/`는 `.gitignore`(로컬 검증)
5. CLAUDE.md 매 응답 전 복잡도 판단 (Track A/B/C)

---

**문서 버전**: v5.2 / **최종 업데이트**: 2026-06-30 / **다음 차수 후보**: 푸시·클라통지(C/D) → Force-Logout 활성화(B) → RBAC 잔여 plan(A)

## 세션 상태

- **활성 세션 수**: 1
- **현재 세션 ID**: ppid-86536
- **충돌 여부**: 없음
- **활성 세션 목록**: ppid-86536

