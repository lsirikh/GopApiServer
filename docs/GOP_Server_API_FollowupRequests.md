# GOP API 서버팀 — 후속 처리 요청 (계정 연동 완전화)

> **배경**: 2026-06-24 회신(`GOP_Server_API_OpenQuestions_RESPONSE.md`) 감사합니다. 코드 실측까지 해주셔서 클라이언트 설계를 거의 다 잠갔습니다.
> **목적**: .NET 클라이언트는 계정/인증/권한/세션/감사 기능을 **보류 없이 전부 연동**하려고 합니다. 이를 위해 아래 서버측 처리(이미 약속분 일정 확정 + 신규 요청)를 부탁드립니다.
> **작성일**: 2026-06-24 / **작성**: .NET 통합 UI 팀

---

## A. 이미 약속해 주신 항목 — 일정 확정 요청

| ID | 항목 | 회신 근거 | 예정 | 요청 |
|---|---|---|---|---|
| **A-1** | `PUT /api/users/me` **photo_url 처리 버그** 수정 | C-5 (v4.7 핫픽스) | 06-30 | 일정 준수 확인. **추가**: photo_url은 URL 문자열인데 **실제 이미지 바이너리 업로드/호스팅 엔드포인트**(multipart)가 명세에 없습니다 — 제공 계획/경로를 알려주세요. (없으면 클라가 로컬 보관 유지) |
| **A-2** | **`permissions.modules` enum 확정** (모듈 키 전수 + 동사 매트릭스) + 시드/스키마/명세 3원 정렬 | B-3, G-08 (v4.8 P0) | 07-11 | **그룹 권한 *편집* UI의 유일한 블로커**입니다. 일정 준수 + **enum 초안을 결재 전 미리 공유**해 주시면 클라가 선구현하겠습니다. |
| **A-3** | `ROLE_CHANGED` / `GROUP_ASSIGNED` 감사 트리거 분리 | B-7, G-07 (v4.8) | v4.8 | 감사 뷰어가 역할/그룹 변경을 별도 식별하려면 필요. |
| **A-4** | 401 envelope 명세 정정 · `WWW-Authenticate` 헤더 복원 · refresh `type` 가드 | G-02 / G-10 / G-11 (v4.7) | 06-30 | 클라는 envelope 기준으로 구현하나, 명세 정정/헤더 복원 확인 요청. |

---

## B. 신규 요청 — 전체 연동을 위해 추가로 필요한 서버 작업

> 회신에서 "v4.x 패치 권고" / "별도 결재 사항" 으로 분류된 것들입니다. **결재 + 일정**을 요청드립니다.

### B-1. 🔴 access_token 강제 무효화 (보안)
- **현황**: 로그아웃·계정잠금·비밀번호변경 후에도 access_token이 만료(24h)까지 유효 (F01-S-01, F07-01). `/me` 도 세션 검증 안 함(F04-I01).
- **요청**: logout / lock / password-change / reset-password 시 **서버측 토큰 무효화**(jti 블랙리스트 또는 세션 검증). 최소한 G-11(refresh jti 블랙리스트)를 **access_token까지 확장**.
- **사유**: 클라 측 토큰 폐기만으로는 탈취 토큰을 막을 수 없음.

### B-2. 🔴 강제 로그아웃 실시간 신호 (NATS SESSION_FORCED_LOGOUT)
- **현황**: 강제 로그아웃(`DELETE /user-sessions/...`) 발생을 대상 클라가 실시간으로 알 방법이 없음. F-1 채널이 "별도 결재 사항".
- **요청**: NATS **`SESSION_FORCED_LOGOUT` push 채널 확정** — topic 이름, payload 구조(`session_id`/`user_id` 필드명), 발행 시점.
- **사유**: 관리자 강제 로그아웃이 즉시 반영되어야 보안 의미가 있음(GOP-06).

### B-3. 🔴 서버측 RBAC 게이트 (보안 defense-in-depth)
- **현황**: `lock`/`unlock`/`DELETE /users/{id}`/`reset-password` 에 role 검증 게이트 부재 → **OPERATOR/VIEWER도 ADMIN 대상 호출 가능** (C-2/C-3/C-6).
- **요청**: 관리 엔드포인트에 **서버측 role 권한 검증** 추가.
- **사유**: 현재 권한 방어선이 클라 UI 게이트뿐 → 우회 가능. 서버 이중 방어 필요.

### B-4. 🟡 login_id 사전 중복확인 엔드포인트
- **현황**: 전용 엔드포인트 없음. POST 시 400 으로만 확인 (C-7).
- **요청**: `GET /api/users/check-login-id?login_id=X` (또는 동등) 신설.
- **사유**: 등록 폼 실시간 중복 검증 UX.

### B-5. 🟡 로그인 이력 조회 엔드포인트
- **현황**: `UserLoginLog` 는 기록되나 조회 API 부재 (C-8).
- **요청**: `GET /api/users/{id}/login-history`(페이징) 또는 `GET /api/auth/login-logs`.
- **사유**: 마이페이지/감사에서 본인·사용자 로그인 이력 화면.

### B-6. 🟡 계정 잠금 메타데이터 영속
- **현황**: 수동 lock 시 `lock_reason`/`locked_at`/`locked_by` 미저장 (C-2, 명세 §9.6.4와 drift).
- **요청**: `POST /users/{id}/lock` 에 `lock_reason`(선택) 바디 + `locked_at`/`locked_by` 기록.
- **사유**: 잠금 사유 표시·감사 추적.

### B-7. 🟡 permissions를 `/users/me`(+refresh)에 포함
- **현황**: permissions는 `POST /auth/login` 응답에만. me·refresh에는 없음 → 권한 갱신 시 `GET /user-groups/{group_id}` 별도 호출 필요 (A-3/A-4/B-1 caveat).
- **요청**: `GET /api/users/me` 응답에 **`permissions` 포함**(가능하면 refresh 응답에도). login/me 일관성 확보.
- **사유**: 권한 변경 후 재조회를 단일 호출로.

### B-8. 🟡 목록 응답 페이지네이션 meta
- **현황**: `GET /user-groups`, `/user-groups/{id}/users`, `/user-sessions` 등 목록에 `total`/`total_pages` 미반환 (B-4/B-5).
- **요청**: 목록 응답 `meta` 에 `total`/`total_pages` 포함.
- **사유**: 클라 페이지네이션 UI.

---

## C. 우선순위 / 회신 요청

| 우선 | 항목 | 비고 |
|---|---|---|
| **P0** | A-2(enum 초안 선공유) · B-1(토큰 무효화) · B-2(강제로그아웃 NATS) · B-3(서버 RBAC) | 보안 + 권한편집 블로커 |
| P1 | A-1(photo 업로드 경로) · B-4 · B-5 · B-6 · B-7 · B-8 | 기능 완전화 |

- **요청**: B-1~B-8 각 항목의 **결재 여부 + 목표 버전/일자**를 회신 부탁드립니다.
- 특히 **A-2 enum 초안**과 **B-1/B-2(보안·강제로그아웃)** 은 클라 구현 착수 전 확정이 필요합니다.

---

문의: 본 문서 댓글 또는 PR 채널로 회신 부탁드립니다. — .NET 통합 UI 팀
