# GUIDE — RBAC 활성화(P5) API측 진행 + 클라 배포 가이드

> **대상**: .NET 클라이언트팀(Dotnet.Monitoring.Solution / Ironwall.Dotnet.Libraries / Dotnet.Rtsp.Viewer.Ui) + 서버팀
> **상태**: 서버측 휴면 RBAC **배포 완료**(2026-06-30, Swagger 5.2.0). 활성화(P5)는 **클라 Bearer 동시배포 후** 진행.
> **연관**: [PRD_GOP_Server_RBAC_Enforcement.md](PRD_GOP_Server_RBAC_Enforcement.md) · [RBAC_Enforcement-prd-plan.md](../plans/RBAC_Enforcement-prd-plan.md) · 상위 클라 PRD: GOP_Permission_Enforcement-prd.md
> **문서 버전**: v5.2-rbac-activation-1 / 작성일: 2026-06-30

---

## 0. 한눈 요약 (두괄식)

| 항목 | 내용 |
|---|---|
| **지금** | 서버에 RBAC 코드가 **휴면(dormant)** 배포됨. `AUTH_MODE=public` 이라 **아무것도 막지 않음**(현 동작 100%). |
| **P5 활성화** | `.env AUTH_MODE=public→token` 플립 **1줄**로 전 API 집행 시작. 코드 변경 없음. |
| **★클라 필수 선행** | 플립 시 **모든 API 호출(읽기 포함)에 `Authorization: Bearer <token>` 필수**. 안 붙은 호출은 전부 **401**. → 클라가 Bearer 부착 배포를 **먼저** 끝내야 함. |
| **집행 2단계** | ① 인증(토큰 유무) = **401** ② 인가(역할 권한) = **403**. 둘을 구분 처리. |
| **롤백** | 문제 시 `AUTH_MODE=public` 복귀 + 컨테이너 재기동 = 즉시 원복(무중단 수준). |

> ⚠️ **가장 흔한 오해**: "쓰기 API만 토큰 필요"가 **아님**. token 모드에서는 **조회(GET) 포함 전 엔드포인트**가 토큰을 요구한다(아래 §3). 쓰기에는 추가로 권한(403) 검사가 붙는다.

---

## 1. 동작 모델 — public vs token

| 상황 | public 모드(현재) | token 모드(P5 이후) |
|---|---|---|
| 토큰 없이 GET | 200 (통과) | **401** Authentication required |
| 토큰 없이 POST/PUT/PATCH/DELETE | 200 (통과) | **401** |
| 유효 토큰 + 권한 있음 | 200 | 200 |
| 유효 토큰 + 권한 없음(저권한 역할) | 200 | **403** Insufficient permission |
| 폐기/로그아웃된 토큰(jti 블랙리스트) | (무시) | **401** `SESSION_REVOKED` |

- 서버 권위 집행 지점 = **모든 write 엔드포인트의 RBAC**(클라 UI 게이팅은 보조·UX). curl 우회는 서버에서만 차단.
- ADMIN 역할은 권한 매트릭스 **무관 통과**(bypass).

---

## 2. 권한 매트릭스 — 엔드포인트 → module:verb

쓰기 엔드포인트 27개에 `require_perm_optional(module, verb)` 휴면 부착 완료. token 모드에서 활성.

| 도메인(라우터) | 경로 prefix | module | POST(생성) | PATCH(수정) | PUT(교체) | DELETE(삭제) |
|---|---|---|---|---|---|---|
| Cameras | `/api/devices/cameras` | `cameras` | edit | edit | edit | delete |
| Sensors | `/api/devices/sensors` | `devices` | edit | edit | edit | delete |
| Controllers | `/api/devices/controllers` | `devices` | edit | edit | edit | delete |
| Detections | `/api/events/detections` | `events` | edit | edit | edit | delete |
| Malfunctions | `/api/events/malfunctions` | `events` | edit | edit | edit | delete |
| Actions | `/api/events/actions` | `events` | edit | edit | edit | delete |
| Servers | `/api/servers` | `servers` | edit | **(ADMIN 전용)** | edit | delete |

- **Servers PATCH** 는 `require_admin`(ADMIN 전용, 더 엄격) — 권한 매트릭스가 아니라 역할=ADMIN 필요.
- **계정/세션/그룹**(users/user-groups/user-sessions) 은 이미 `require_admin` 집행 중(public 모드에서도). 변동 없음.
- **Reports** 는 이미 `require_perm`(엄격, AUTH_MODE 무관 토큰 필수) 집행 중.
- **Audit-logs** 는 read-only(write 없음).
- verb 의미: `view`(조회) · `edit`(생성/수정) · `delete`(삭제) · `control`(cameras 전용 PTZ/제어).

### 모듈 표기 계약 (클라 오기 방지)
서버 모듈 키: `devices · events · cameras · reports · users · user_groups · audit_logs · servers · map · broadcast · setup_system · setup_feature`.
**`cameras`** 표기 통일(클라 `cam` 오기 금지).

---

## 3. ★ 클라이언트 필수 작업 (배포 체크리스트)

> 이 항목이 **P5 활성화의 선행 조건**. 미완 상태로 서버가 플립하면 클라 전체 401.

- [ ] **모든 API 호출에 Bearer 부착**: Device/Event/Camera/Server/조회 포함 **전 ApiService** 에 `Authorization: Bearer <access_token>` 헤더 주입(BearerAuthHandler).
  - 읽기(GET)도 포함 — token 모드는 인증 전면 요구.
- [ ] **로그인/토큰 보관**: `POST /api/auth/login` → `data.access_token` + `data.refresh_token` + `data.session_id` 저장.
- [ ] **토큰 갱신**: access 만료 임박 시 `POST /api/auth/refresh`(refresh_token) 로 회전. (sid 고정, jti 회전 — 계약 [CONTRACT_GOP_Server_v5.2.md](CONTRACT_GOP_Server_v5.2.md) C1)
- [ ] **401 처리**: `401` 수신 → 토큰 만료/무효/폐기 → **재로그인 플로우**. 특히 `error.code=SESSION_REVOKED` 는 강제로그아웃됨 → 즉시 로그아웃 UI(재시도 금지).
- [ ] **403 처리**: `403 Insufficient permission: requires {module}:{verb}` → **권한 부족**(재시도 금지) → 사용자에게 권한없음 안내. 재로그인 대상 아님.
- [ ] **(권장) UI 게이팅**: 역할별 권한 매트릭스로 버튼/메뉴 비활성(서버 403 전에 UX 차단). 단 **서버가 권위** — UI 게이팅은 보조.

---

## 4. 서버측 활성화 절차 (P5 cutover)

> 클라 §3 배포 + 확인 완료 후에만 실행.

1. **사전 점검**
   - [ ] **V-SV-01 이주율**: `account_users` 계정 이주 확인(레거시 계정으로 인한 401 급증 방지).
   - [ ] **역할별 권한 매트릭스 시드 확인**: 각 역할(OPERATOR/MAINTAINER/VIEWER)의 등급 그룹 `permissions.modules` 가 의도대로 채워졌는지. (미정의 모듈 → 해당 역할 영구 403) ※ ADMIN 은 bypass 라 무관.
   - [ ] 클라 §3 Bearer 부착 배포 **완료 확인**.
2. **플립**: `.env` 의 `AUTH_MODE=public` → `AUTH_MODE=token`.
3. **재기동**: `docker compose up -d api-server` (코드 재빌드 불필요 — 휴면 코드 이미 배포됨).
4. **검증(NFR-SV-01/02)**:
   - 무토큰 GET/POST → **401**.
   - VIEWER 토큰으로 `POST /api/devices/cameras` → **403**.
   - OPERATOR 토큰(cameras:edit 보유)으로 동일 → **200/201**.
   - 로그아웃 후 구 토큰 → **401** `SESSION_REVOKED`.
5. **롤백 기준**: 정상 클라의 광범위 401 발생 시 → `.env AUTH_MODE=public` 복귀 + 재기동(즉시 원복). 안전점: git `v5.2-pre-deploy` / 이미지 `api-test-server:pre-v5.2`.

---

## 5. 단계적 롤아웃(선택)

전면 플립이 부담되면 도메인별 점진 활성화 가능(서버 작업):
- 휴면 의존성을 도메인 단위로 `require_perm`(엄격)으로 승격하거나, AUTH_MODE 플립 전 특정 라우터만 강제.
- 단, **AUTH_MODE=token 은 전역 스위치**라 부분 적용 불가 → 부분 롤아웃이 필요하면 라우터별 엄격 의존성으로 전환하는 별도 설계 필요.
- **권고**: 클라 Bearer 부착이 전 ApiService 에 적용되면 전역 플립이 가장 단순·일관.

---

## 6. 미해결/PM 결정 대기

| 항목 | 내용 |
|---|---|
| OQ-PG-04 | `cam:imaging` 별도 토큰 여부 → 서버 PermissionsSchema 영향 |
| OQ-PG-06 | GUEST 폐지 시 EnumUserRole/시드 영향 |
| OQ-PG-07 | 비ADMIN 본인삭제 `DELETE /users/me` 설계 |
| 역할 기본 매트릭스 | OPERATOR/MAINTAINER/VIEWER 의 모듈별 view/edit/delete/control 기본값 확정(클라 UI 게이팅과 동일 표 사용) |

---

**요청(클라팀)**: §3 체크리스트 적용 + §2 권한 매트릭스를 UI 게이팅에 반영, §6 역할 기본 매트릭스 확정 회신. 회신·배포 확인 후 서버가 §4 플립 진행.
