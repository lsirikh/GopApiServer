# Plan — RBAC Enforcement (FR-SV-04/08) 배포-대기형 롤아웃

> 기준 PRD: [`../prds/PRD_GOP_Server_RBAC_Enforcement.md`](../prds/PRD_GOP_Server_RBAC_Enforcement.md)
> 작성일: 2026-06-30 / 차수: v5.x (feature/tracking-gis-ingest)
> 핵심 전략: **휴면(dormant) 집행** — 코드는 지금 배포, 활성화는 클라 Bearer 동시배포일 `AUTH_MODE=token` 플립으로.

---

## 0. 설계 결정 (두괄식)

| 결정 | 내용 | 근거 |
|---|---|---|
| **휴면 집행** | `require_perm_optional(module, verb)`: AUTH_MODE=public 무집행(현 동작 100% 보존), token 플립 시에만 활성 | 현 `.env AUTH_MODE=public` + 클라 3종 Bearer 미부착 → 즉시 부착 시 전원 401. 휴면이면 안전 배포 |
| **권한 원천** | 역할명 등급그룹 매트릭스(`UserGroup.name==role`) → 폴백 `group_id` (OQ-PG-01 Option A) | 로그인 권한 유도와 동일 원천 → UI/서버 일관 |
| **이주 무위험** | 8 라우터 write 핸들러가 `get_current_user_optional` 결과를 **전부 미사용**(Explore 검증) → 데코레이터 `dependencies=[]` 부착만으로 충분, User→AccountUser 속성 깨짐 없음 | FR-SV-08 리스크 소거 |

---

## 1. 권한 매핑 (27 write 엔드포인트 부착 완료)

| 라우터 | 모듈 | POST | PATCH | PUT | DELETE |
|---|---|---|---|---|---|
| cameras | `cameras` | edit | edit | edit | delete |
| sensors | `devices` | edit | edit | edit | delete |
| controllers | `devices` | edit | edit | edit | delete |
| actions | `events` | edit | edit | edit | delete |
| detections | `events` | edit | edit | edit | delete |
| malfunctions | `events` | edit | edit | edit | delete |
| servers | `servers` | edit | *(require_admin 유지)* | edit | delete |
| audit_logs | — | *(write 없음, read-only)* | | | |

> servers PATCH 는 기존 `require_admin`(ADMIN 전용, 더 엄격) 유지. audit_logs write 없음 → FR-SV-04 대상 외(FR-SV-07 별도).

---

## 2. 단계 (Phase)

- [x] **P0 — 인프라** (기구축 확인): `require_perm`·`get_current_account_user_optional`·jti 검사 (auth.py). FR-SV-01/05/06 기구현 확인.
- [x] **P1 — 구조**: require_perm 매트릭스 로직 헬퍼 추출(`_resolve_role_group`·`_role_group_allows`). `c49f0a4`
- [x] **P2 — 휴면 의존성**: `require_perm_optional` 추가 + 단위테스트 5/5. `9a6...`(auth) 
- [x] **P3 — 부착**: 27 write 데코레이터 휴면 부착, 도메인 회귀 0(사전실패 카운트 전후 동일). `9a6624c`
- [x] **P4 — FR-SV-10**: 비번변경 시 본인 타 세션 무효화. `b2f80c8`
- [ ] **P5 — 활성화(★게이트, 본 세션 외)**: 클라 Bearer 동시배포 확인 → `.env AUTH_MODE=public→token` 플립. 분리 시 비계정 전원 401.
- [ ] **P6 — FR-SV-07**: audit DELETE 405 stub + PostgreSQL RULE/RLS DB레벨 DELETE 거부 + APScheduler purge (마이그레이션 필요).
- [ ] **P7 — FR-SV-11**: GET /cameras RTSP URL 을 `cameras:view` 없는 역할에 마스킹 (응답 변경=반파괴, 클라 조율).
- [ ] **P8 — FR-SV-09**: user_groups GET `require_admin` 점검 보강.

---

## 3. 활성화(P5) 전제 — ★배포 주의

1. **클라(.NET 3종)** Device/Event/Camera ApiService 에 Bearer 부착(상위 PRD GOP_Permission_Enforcement) 배포 확인.
   - 소비처: `Dotnet.Monitoring.Solution` / `Ironwall.Dotnet.Libraries` / `Dotnet.Rtsp.Viewer.Ui`.
2. **V-SV-01** account_users 이주율 확인(전환 전 레거시 401 급증 방지).
3. 위 1·2 충족 후 `.env AUTH_MODE=token` + 컨테이너 재기동. 롤백 = `AUTH_MODE=public` 복귀(즉시).
4. **NFR-SV-01 검증**: curl 비인증/저권한 퍼징 → 401/403 확인. 도메인별 구토큰 401(NFR-SV-02).

---

## 4. 검증 상태

- 단위: `tests/test_require_perm_optional.py` 5/5 (휴면 통과·ADMIN·권한보유·무권한403·무토큰401).
- 회귀: 7 도메인 write 테스트 — 부착 전후 동일(사전실패 3 failed+1 error는 pydantic/env 무관 이슈).
- ⬜ token-모드 통합(실 라우터 403/401)은 client 픽스처가 public 강제라 별도 무override 클라이언트 필요 — **P5 활성화 시 curl 라이브 검증**으로 대체.

---

## 5. 잔여(별도 차수/조율)

| 항목 | 유형 | 비고 |
|---|---|---|
| P5 AUTH_MODE 플립 | 조율 | 클라 동시배포 |
| P6 FR-SV-07 audit DB | 마이그레이션 | RULE/RLS + purge |
| P7 FR-SV-11 RTSP 마스킹 | 반파괴 | 응답 변경, 클라 영향 검토 |
| P8 FR-SV-09 | 소 | user_groups GET 점검 |
