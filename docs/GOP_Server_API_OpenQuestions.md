# GOP API 서버팀 확인 요청 (계정 연동)

> **배경**: 클라이언트(Ironwall WPF)에서 GOP REST API의 **계정/인증/권한/세션/감사** 연동을 구현하기 위한 사전 확인 사항입니다.
> **기준 문서**: `GOP_Restful_Api_연동설계.md` v4.8 (2026-06-22) §4.5~4.6, §9.1~9.6
> **우선순위**: 🔴 = 인증/권한 코어 설계가 막힘(선행 필수) · 🟡 = 후속 기능 구현 시 필요
> **작성일**: 2026-06-24

---

## A. 인증 / 토큰 (Auth, Token)

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| A-1 | `access_token`·`refresh_token`의 **만료 시간(TTL)** 은 각각 얼마인가요? | 🔴 | 토큰 저장소·선제 갱신(만료 N분 전)·자동 재발급 로직 설계에 수치 필요. 명세에 TTL 미기재. |
| A-2 | **401 응답 body 구조**가 `{detail: "..."}` 인가요, 공통 `{success:false, error:{code,message}}` 인가요? 엔드포인트마다 다른가요? | 🔴 | BearerAuthHandler가 401을 감지해 refresh를 트리거하므로 응답 파싱 규격 확정 필요. |
| A-3 | `POST /api/auth/refresh` **응답에 갱신된 `permissions`(또는 user)가 포함**되나요, `access_token`/`refresh_token`만 오나요? | 🔴 | 토큰 갱신 후 권한 상태를 다시 반영해야 하는지 결정. |
| A-4 | `GET /api/auth/me`(flat) 응답에 **`permissions`가 포함**되나요? `GET /api/users/me`(envelope)와 구조가 다른가요? | 🔴 | 본인 정보 DTO 역직렬화 경로(2종) 분기 설계에 필요. |
| A-5 | 본인 프로필 **1차 조회**는 `GET /api/auth/me` 와 `GET /api/users/me` 중 어느 것을 표준으로 사용해야 하나요? | 🟡 | MyPage 초기 로드 경로 결정. |

---

## B. 권한 / 그룹 (Permission, UserGroup) — **가장 중요**

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| B-1 | 로그인/me 응답의 `permissions`는 **그룹 상속까지 반영된 최종값(flattened)** 인가요, 아니면 클라이언트가 그룹 권한과 병합해야 하나요? | 🔴 | 클라가 권한 병합 로직을 가질지(IPermissionService 복잡도) 결정하는 핵심. |
| B-2 | **개인(user) 권한과 그룹(group) 상속 권한이 충돌**할 때 서버 우선순위 정책은? (개인 오버라이드 가능 여부) | 🔴 | 권한 판정 규칙·UI 표시 방식의 근거. |
| B-3 | `permissions.modules`의 **전체 모듈 키 목록**과 모듈별 **유효 동사**(view/edit/delete/control 중 어떤 조합)는? (현재 `events`, `cameras`만 확인됨) | 🔴 | 권한 매트릭스 데이터 모델·그룹 편집 UI 구성에 필요. |
| B-4 | `GET /api/user-groups`(목록) 지원 **쿼리 파라미터(페이지/필터)** 와 응답 스키마는? | 🟡 | 그룹 목록 화면 구현 범위. |
| B-5 | `GET /api/user-groups/{id}/users` 응답 스키마(포함 필드)는? | 🟡 | 그룹 소속 사용자 표시. |
| B-6 | **그룹 삭제 시 소속 사용자** 처리는 cascade(orphan) 인가요, block 인가요? | 🟡 | 삭제 확인 UX/에러 처리. |
| B-7 | `GROUP_ASSIGNED` / `ROLE_CHANGED` 감사 액션을 트리거하는 **엔드포인트**는? (§9.6.4 자동 트리거 표에 누락) | 🟡 | 역할/그룹 변경 경로 확인. |

---

## C. 사용자 / 계정 (User CRUD, Lock, Password)

> 명세서에 **요청 바디가 빠진 엔드포인트**들입니다. 정확한 필드 목록(필수/선택, nullable)이 필요합니다.

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| C-1 | `PUT /api/users/{id}` **요청 바디 필드** 전체 — `password` 포함 여부, `role`/`group_id` 변경 가능 여부, nullable 처리 | 🟡 | 사용자 수정 DTO 작성. |
| C-2 | `POST /api/users/{id}/lock` 바디에 **`lock_reason`** 이 있나요(필수/선택)? `unlock` 은 빈 바디 POST 인가요? | 🟡 | 계정 잠금/해제 UI(신규 기능) 구현. |
| C-3 | `POST /api/users/{id}/reset-password`(관리자 강제) — **`new_password` 를 직접 보내나요, 서버가 임시비번을 생성해 응답에 반환**하나요? 반환 시 응답 채널(body/이메일)? | 🟡 | 비번 초기화 UX. (현재 앱은 하드코딩 임시비번 → 제거 예정) |
| C-4 | `PUT /api/users/me/password`(본인) 바디 필드는 **`current_password` + `new_password`** 두 개가 맞나요? | 🟡 | 본인 비번 변경 DTO. |
| C-5 | `PUT /api/users/me`(본인 프로필) 요청 바디 필드는? | 🟡 | MyPage 저장 DTO. |
| C-6 | **본인 self-DELETE** 가 허용되나요? | 🟡 | 삭제 가드. |
| C-7 | **아이디 중복 확인** 전용 API가 있나요? (예: `HEAD /api/users/check/{login_id}`) 없으면 목록 조회로 대체해야 하나요? | 🟡 | 등록 폼 실시간 검증. |
| C-8 | **로그인 이력 조회/기록 API** 가 있나요? (마지막 로그인 복원·기록용) 없으면 클라 로컬 보관을 허용하나요? | 🟡 | `GetLatestLogin`/`RecordLogin` 대응 전략. |

---

## D. 세션 (UserSession)

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| D-1 | **강제 로그아웃**(`DELETE /api/user-sessions/...`) 발생 시, 대상 클라이언트가 이를 **실시간으로 수신**해야 하나요? 수신 채널(NATS topic / WebSocket)과 payload는? | 🔴 | GOP-06 강제 로그아웃 반영의 핵심(아래 F-1과 연동). |
| D-2 | `GET /api/user-sessions` 에 **`user_id` 필터** 가 지원되나요? | 🟡 | 특정 사용자 세션만 조회. |
| D-3 | 세션 `expires_at` 의 **타임존 규격**(UTC / ISO8601 offset)은? | 🟡 | 만료 표시·계산 정확도. |

---

## E. 감사 로그 (Audit Log)

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| E-1 | 조회 필터 `start_date`/`end_date` 의 **타임존 규격**(ISO8601 offset 필수? 서버 로컬 vs UTC)은? | 🟡 | 기간 필터 정확도. |
| E-2 | `error_message` 필드는 **`FAILURE` 상태 로그에만** 포함되나요? | 🟡 | 감사 뷰어 컬럼 처리. |
| E-3 | `SESSION_CREATED`/`SESSION_TERMINATED` 감사 로그는 **로그인/로그아웃 API 호출 시 자동 생성**되나요, 별도 경로인가요? (§9.6.4 트리거 표에 없음) | 🟡 | 감사 데이터 완전성 확인. |

---

## F. 실시간 / NATS (Session Resilience)

| # | 질문 | 우선 | 왜 필요한가 |
|---|------|:--:|------|
| F-1 | **`SESSION_FORCED_LOGOUT`** NATS 이벤트의 정확한 **payload 구조**(topic 이름, `session_id`/`user_id` 필드명)는? | 🔴 | 강제 로그아웃 수신 핸들러 구현(GOP-06 FR-SRL-03). |

---

### 회신 요청
- 🔴 (A-1~4, B-1~3, D-1, F-1) 은 **인증/권한 코어 설계 선행 필수** → 우선 회신 부탁드립니다.
- 명세서에 이미 반영된 항목이면 해당 **섹션 번호만** 알려주셔도 됩니다.
